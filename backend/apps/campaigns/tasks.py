import logging
import random
import time
from celery import shared_task
from django.db import transaction, models
from django.utils import timezone
from tenant_schemas_celery.task import TenantTask

from apps.campaigns.models import Campaign, CampaignItem
from apps.whatsapp.services.whatsapp_service import whatsapp_service
from core.utils import render_template_variables

logger = logging.getLogger(__name__)


@shared_task(bind=True, base=TenantTask, queue='campaigns')
def process_campaign_batch(self, campaign_id):
    """
    Processa um lote de mensagens de uma campanha.
    Executa sequencialmente com delay para respeitar rate limits.
    Ao final, se houver mais itens, agenda o próximo lote.
    """
    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        logger.error(f"Campanha {campaign_id} não encontrada.")
        return

    if campaign.status != Campaign.Status.RUNNING:
        logger.info(f"Campanha {campaign_id} parada ou finalizada. Status: {campaign.status}")
        return

    # Tamanho do lote
    BATCH_SIZE = 10

    # Busca itens pendentes
    # select_for_update com skip_locked garante que se tivermos multiplos workers,
    # eles não peguem os mesmos itens (embora a ideia seja serializar por campanha)
    with transaction.atomic():
        items = list(
            CampaignItem.objects.filter(
                campaign=campaign,
                status=CampaignItem.Status.PENDING
            ).select_for_update(skip_locked=True)[:BATCH_SIZE]
        )

        # Marca como QUEUED para evitar que outra task pegue
        for item in items:
            item.status = CampaignItem.Status.QUEUED
            item.save(update_fields=['status'])

    if not items:
        # Nenhum item pendente encontrado.
        # Verifica se ainda existem itens pendentes totais (talvez bloqueados)
        pending_count = CampaignItem.objects.filter(
            campaign=campaign,
            status=CampaignItem.Status.PENDING
        ).count()

        if pending_count == 0:
            # Campanha concluída
            campaign.status = Campaign.Status.COMPLETED
            campaign.completed_at = timezone.now()
            campaign.save()
            logger.info(f"Campanha {campaign.name} concluída!")
        else:
            # Ainda há itens pendentes (possivelmente bloqueados), agenda próxima tentativa
            logger.info(f"Ainda há {pending_count} itens pendentes, aguardando...")
            process_campaign_batch.apply_async(args=[campaign_id], countdown=5)
        return

    logger.info(f"Processando lote de {len(items)} mensagens para campanha {campaign.name}")

    # Processa o lote
    for item in items:
        # Verifica se campanha foi pausada durante o processamento do lote
        campaign.refresh_from_db()
        if campaign.status != Campaign.Status.RUNNING:
            break

        try:
            # 1. Calcular Delay
            msg_length = len(campaign.message)
            if msg_length < 100:
                delay = random.uniform(2, 4)
            elif msg_length < 300:
                delay = random.uniform(5, 8)
            else:
                delay = random.uniform(10, 15)

            logger.info(f"Aguardando {delay:.2f}s para enviar mensagem...")
            time.sleep(delay)

            # 2. Preparar contexto e renderizar mensagem
            context = {
                'name': item.recipient_name or '',
                'first_name': item.recipient_name.split()[0] if item.recipient_name else '',
            }

            # Adicionar informações adicionais do supporter se disponível
            if item.supporter:
                context.update({
                    'city': item.supporter.city or '',
                    'neighborhood': item.supporter.neighborhood or '',
                    'state': item.supporter.state or '',
                })

            # Renderizar mensagem com variáveis
            final_message = render_template_variables(campaign.message, context)

            # 3. Enviar Mensagem
            response = whatsapp_service.send_text_sync(
                instance_name=campaign.whatsapp_session.instance_name,
                phone=item.recipient_phone,
                text=final_message,
                api_key=campaign.whatsapp_session.access_token
            )

            # 4. Atualizar Item
            item.status = CampaignItem.Status.SENT
            item.sent_at = timezone.now()
            # Tenta pegar ID da mensagem da resposta da Evolution
            if isinstance(response, dict) and 'key' in response:
                 item.message_id = response['key'].get('id')
            item.save()

            # 5. Atualizar Métricas da Campanha
            Campaign.objects.filter(pk=campaign.id).update(
                messages_sent=models.F('messages_sent') + 1
            )

            logger.info(f"Mensagem enviada para {item.recipient_name} ({item.recipient_phone})")

        except Exception as e:
            logger.error(f"Erro ao enviar item {item.id}: {str(e)}")
            item.status = CampaignItem.Status.FAILED
            item.error_message = str(e)
            item.save()

            Campaign.objects.filter(pk=campaign.id).update(
                messages_failed=models.F('messages_failed') + 1
            )

    # Verifica se ainda há itens pendentes antes de agendar próximo lote
    remaining_count = CampaignItem.objects.filter(
        campaign=campaign,
        status=CampaignItem.Status.PENDING
    ).count()

    if remaining_count > 0:
        logger.info(f"Restam {remaining_count} itens. Agendando próximo lote...")
        process_campaign_batch.apply_async(args=[campaign_id], countdown=2)
    else:
        logger.info(f"Todos os itens foram processados. Finalizando campanha {campaign.name}.")
        campaign.status = Campaign.Status.COMPLETED
        campaign.completed_at = timezone.now()
        campaign.save()
