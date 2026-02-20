"""
Celery tasks for WhatsApp webhook processing.
"""
import logging

from celery import shared_task
from django.utils import timezone
from tenant_schemas_celery.task import TenantTask

logger = logging.getLogger(__name__)


@shared_task(bind=True, base=TenantTask, queue='webhooks')
def process_webhook(self, webhook_log_id: int) -> None:
    """
    Processa um webhook recebido da Evolution API.

    Args:
        webhook_log_id: ID do WebhookLog a processar
    """
    from apps.whatsapp.models import WebhookLog, WhatsAppSession
    from apps.messaging.models import Message

    try:
        webhook_log = WebhookLog.objects.get(id=webhook_log_id)
    except WebhookLog.DoesNotExist:
        logger.error(f"WebhookLog {webhook_log_id} não encontrado")
        return

    try:
        event_type = webhook_log.event_type
        payload = webhook_log.payload

        logger.info(f"Processando webhook {event_type} para sessão {webhook_log.session.name}")

        if event_type == 'qrcode.updated':
            _handle_qrcode_updated(webhook_log.session, payload)

        elif event_type == 'connection.update':
            _handle_connection_update(webhook_log.session, payload)

        elif event_type == 'messages.update':
            print("="*20)
            print("DEBUG - messages.update payload:")
            print(payload)
            _handle_messages_update(payload)

        elif event_type == 'send.message':
            _handle_send_message(payload)

        webhook_log.mark_as_processed()
        logger.info(f"Webhook {webhook_log_id} processado com sucesso")

    except Exception as e:
        logger.exception(f"Erro ao processar webhook {webhook_log_id}: {e}")
        webhook_log.mark_as_processed(error=str(e))


def _handle_qrcode_updated(session, payload: dict) -> None:
    """Atualiza QR Code da sessão."""
    session.status = 'connecting'
    session.save(update_fields=['status', 'updated_at'])
    logger.info(f"QR Code atualizado (ignorado armazenamento) para sessão {session.name}")


def _handle_connection_update(session, payload: dict) -> None:
    """Atualiza status de conexão da sessão."""
    from apps.whatsapp.models import WhatsAppSession

    state = payload.get('state', payload.get('connection', '')).lower()

    if state in ['open', 'connected']:
        session.status = WhatsAppSession.Status.CONNECTED
        session.is_healthy = True
        session.last_health_check = timezone.now()

        # Tenta extrair o número conectado
        phone = payload.get('instance', {}).get('wuid', '')
        if phone:
            session.phone_number = phone.split('@')[0]

    elif state in ['close', 'disconnected']:
        session.status = WhatsAppSession.Status.DISCONNECTED
        session.is_healthy = False

    elif state == 'connecting':
        session.status = WhatsAppSession.Status.CONNECTING

    session.save()
    logger.info(f"Conexão atualizada para sessão {session.name}: {session.status}")


def _handle_messages_update(payload: dict) -> None:
    """Atualiza status de mensagens."""
    from apps.messaging.models import Message
    from apps.campaigns.models import CampaignItem

    # Extrai informações do payload
    data = payload.get('data', {})

    # O Evolution API envia diferentes formatos de ID dependendo do evento:
    #
    # Evento 'send.message':
    #   - data.key.id: ID do WhatsApp (ex: 3EB05A28C92F22C240AB20)
    #
    # Evento 'messages.update':
    #   - data.keyId: ID do WhatsApp (ex: 3EB01A138E5C8F68A9BC7D)
    #   - data.messageId: ID interno da Evolution (ex: cmluywje900went4xasoiznu0)
    #
    # Precisamos usar keyId/key.id (WhatsApp ID) para encontrar o CampaignItem
    message_id = data.get('keyId', '')  # messages.update usa keyId (string)
    if not message_id:
        # Fallback para send.message que usa key.id (objeto)
        key = data.get('key', {})
        message_id = key.get('id', '') if isinstance(key, dict) else ''

    status = data.get('status', '').upper()

    logger.info("="*80)
    logger.info(f"📊 MESSAGES.UPDATE - Status: {status}")
    logger.info(f"   Key ID/KeyID (WhatsApp): {message_id}")
    logger.info(f"   Message ID (Evolution): {data.get('messageId', '')}")
    logger.info("="*80)

    if not message_id:
        logger.warning("keyId/key.id não fornecido no webhook")
        # Último recurso: tentar messageId
        message_id = data.get('messageId', '')
        if not message_id:
            logger.warning("messageId também não fornecido")
            return

    # 1. Primeiro tenta atualizar CampaignItem (prioridade para campanhas)
    campaign_item = CampaignItem.objects.filter(
        message_id=message_id
    ).first()

    if not campaign_item:
        logger.info(f"   ⚠️  CampaignItem não encontrado para keyId/key.id: {message_id}")
        # Loga todos os message_ids existentes para debug
        all_message_ids = CampaignItem.objects.filter(
            message_id__isnull=False
        ).values_list('message_id', flat=True)[:10]
        logger.info(f"   📋 Message_ids existentes (primeiros 10): {list(all_message_ids)}")

    if campaign_item:
        campaign = campaign_item.campaign
        logger.info(f"   📢 Campanha: {campaign.name}")
        logger.info(f"   Destinatário: {campaign_item.recipient_name}")
        logger.info(f"   Status anterior: {campaign_item.status}")

        update_fields = ['status', 'updated_at']

        if status == 'DELIVERY_ACK':
            # Mensagem entregue ao destinatário
            campaign_item.delivered_at = timezone.now()
            campaign_item.status = CampaignItem.Status.DELIVERED
            update_fields.extend(['delivered_at'])

            # Atualiza contador da campanha
            campaign.messages_delivered += 1
            campaign.save(update_fields=['messages_delivered'])

            logger.info(f"   ✅ MENSAGEM ENTREGUE para {campaign_item.recipient_name}")

        elif status == 'READ':
            # Mensagem lida pelo destinatário
            campaign_item.read_at = timezone.now()
            campaign_item.status = CampaignItem.Status.READ
            update_fields.extend(['read_at'])

            # Atualiza contador da campanha
            campaign.messages_read += 1
            campaign.save(update_fields=['messages_read'])

            logger.info(f"   📖 MENSAGEM LIDA por {campaign_item.recipient_name}")

        elif status == 'FAILED':
            # Mensagem falhou
            campaign_item.status = CampaignItem.Status.FAILED
            campaign_item.error_message = f"Falha no envio: {status}"

            # Atualiza contador da campanha
            campaign.messages_failed += 1
            campaign.save(update_fields=['messages_failed'])

            logger.info(f"   ❌ MENSAGEM FALHOU para {campaign_item.recipient_name}")

        elif status == 'SERVER_ACK':
            # Mensagem enviada para o servidor do WhatsApp
            if campaign_item.status == CampaignItem.Status.PENDING:
                campaign_item.status = CampaignItem.Status.QUEUED
                campaign_item.sent_at = timezone.now()
                update_fields.extend(['sent_at'])

                logger.info(f"   📤 MENSAGEM ENVIADA para {campaign_item.recipient_name}")

        # Salva CampaignItem
        campaign_item.save(update_fields=update_fields)

        logger.info(
            f"CampaignItem {campaign_item.id} atualizado: "
            f"{campaign_item.status} (msg: {status})"
        )
        logger.info(f"   📊 Estatísticas da Campanha:")
        logger.info(f"      ✉️  Enviadas: {campaign.messages_sent}")
        logger.info(f"      ✅ Entregues: {campaign.messages_delivered}")
        logger.info(f"      📖 Lidas: {campaign.messages_read}")
        logger.info(f"      ❌ Falhas: {campaign.messages_failed}")
        return

    # 2. Se não for CampaignItem, tenta atualizar modelo Message (compatibilidade)
    key = payload.get('key', {})
    alt_message_id = key.get('id', message_id)

    try:
        message = Message.objects.get(whatsapp_message_id=alt_message_id)
    except Message.DoesNotExist:
        # Tenta pelo external_id
        try:
            message = Message.objects.get(external_id=alt_message_id)
        except Message.DoesNotExist:
            logger.info(f"   ⚠️  Message também não encontrado (whatsapp_message_id ou external_id: {alt_message_id})")
            return

    # Atualiza status
    if status in ['DELIVERED', 'DELIVERY_ACK', 'SERVER_ACK']:
        message.mark_as_delivered()
        logger.info(f"Mensagem {message.id} marcada como entregue")

    elif status in ['READ', 'PLAYED']:
        message.mark_as_read()
        logger.info(f"Mensagem {message.id} marcada como lida")

    elif status in ['ERROR', 'FAILED']:
        error_msg = payload.get('message', 'Erro desconhecido')
        message.mark_as_failed(error_message=error_msg)
        logger.warning(f"Mensagem {message.id} falhou: {error_msg}")


def _handle_send_message(payload: dict) -> None:
    """Processa confirmação de envio de mensagem."""
    from apps.messaging.models import Message

    key = payload.get('key', {})
    message_id = key.get('id', '')

    if not message_id:
        return

    # Atualiza o whatsapp_message_id se ainda não tiver
    external_id = payload.get('messageId', '')
    if external_id:
        Message.objects.filter(
            external_id=external_id,
            whatsapp_message_id=''
        ).update(whatsapp_message_id=message_id)


@shared_task(queue='default')
def health_check_sessions() -> None:
    """
    Verifica saúde de todas as sessões ativas.
    Deve ser executada periodicamente via Celery Beat.
    """
    from apps.whatsapp.models import WhatsAppSession
    from apps.whatsapp.services import whatsapp_service

    sessions = WhatsAppSession.objects.filter(
        is_active=True,
        status=WhatsAppSession.Status.CONNECTED
    )

    for session in sessions:
        try:
            is_healthy = whatsapp_service.health_check_sync(session.instance_name)
            session.is_healthy = is_healthy
            session.last_health_check = timezone.now()

            if not is_healthy:
                session.status = WhatsAppSession.Status.DISCONNECTED
                logger.warning(f"Sessão {session.name} não está mais saudável")

            session.save(update_fields=['is_healthy', 'last_health_check', 'status', 'updated_at'])

        except Exception as e:
            logger.exception(f"Erro ao verificar sessão {session.name}: {e}")
            session.is_healthy = False
            session.save(update_fields=['is_healthy', 'updated_at'])


@shared_task(queue='default')
def reset_daily_counters() -> None:
    """
    Reseta contadores diários de mensagens das sessões.
    Deve ser executada às 00:00 via Celery Beat.
    """
    from apps.whatsapp.models import WhatsAppSession

    updated = WhatsAppSession.objects.filter(
        is_active=True
    ).update(messages_sent_today=0)

    logger.info(f"Reset de contadores diários: {updated} sessões atualizadas")
