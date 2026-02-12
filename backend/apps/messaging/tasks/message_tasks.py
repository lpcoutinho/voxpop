"""
Celery tasks for message sending and processing.
"""
import logging

from celery import shared_task
from django.utils import timezone
from tenant_schemas_celery.task import TenantTask

logger = logging.getLogger(__name__)


@shared_task(bind=True, base=TenantTask, queue='messages_high', rate_limit='30/m')
def send_message_task(self, message_id: int) -> None:
    """
    Envia uma mensagem individual via WhatsApp.

    Args:
        message_id: ID da mensagem a enviar
    """
    from apps.messaging.models import Message
    from apps.whatsapp.services import whatsapp_service
    from core.exceptions import EvolutionAPIError

    try:
        message = Message.objects.select_related(
            'whatsapp_session', 'template'
        ).get(id=message_id)
    except Message.DoesNotExist:
        logger.error(f"Mensagem {message_id} não encontrada")
        return

    # Verifica se já foi enviada
    if message.status not in [Message.Status.PENDING, Message.Status.QUEUED]:
        logger.warning(f"Mensagem {message_id} já foi processada: {message.status}")
        return

    # Verifica sessão
    session = message.whatsapp_session
    if not session or not session.can_send_messages:
        message.mark_as_failed(
            error_code='SESSION_UNAVAILABLE',
            error_message='Sessão WhatsApp não disponível'
        )
        return

    try:
        # Envia mensagem
        if message.message_type == 'text':
            result = whatsapp_service.send_text_sync(
                instance_name=session.instance_name,
                phone=message.phone,
                text=message.content,
            )
        else:
            # Envia mídia
            result = whatsapp_service.send_media_sync(
                instance_name=session.instance_name,
                phone=message.phone,
                media_url=message.media_url,
                media_type=message.message_type,
                caption=message.content,
            )

        # Extrai IDs da resposta
        external_id = result.get('key', {}).get('id', '')
        whatsapp_id = result.get('messageId', external_id)

        # Marca como enviada
        message.mark_as_sent(external_id=external_id, whatsapp_id=whatsapp_id)

        # Salva na tabela Message para contagem no dashboard
        from apps.messaging.models import Message
        Message.objects.create(
            supporter=message.supporter,
            campaign_item=message.campaign_item,
            direction='out',
            status=Message.Status.SENT,
            message_type=message.message_type or 'text',
            content=message.content,
            media_url=message.media_url,
            external_id=external_id,
            whatsapp_id=whatsapp_id,
            created_at=timezone.now(),
        )

        # Incrementa contador da sessão
        session.increment_message_count()

        logger.info(f"Mensagem {message_id} enviada com sucesso")

    except EvolutionAPIError as e:
        logger.error(f"Erro ao enviar mensagem {message_id}: {e}")
        message.retry_count += 1
        message.save(update_fields=['retry_count', 'updated_at'])

        # Tenta novamente se ainda tem tentativas
        if message.can_retry:
            raise self.retry(exc=e, countdown=60 * message.retry_count)
        else:
            message.mark_as_failed(
                error_code='API_ERROR',
                error_message=str(e)
            )

    except Exception as e:
        logger.exception(f"Erro inesperado ao enviar mensagem {message_id}: {e}")
        message.mark_as_failed(
            error_code='UNEXPECTED_ERROR',
            error_message=str(e)
        )


@shared_task(bind=True, base=TenantTask, queue='messages_low')
def batch_send_messages(self, message_ids: list[int]) -> dict:
    """
    Envia um lote de mensagens.

    Args:
        message_ids: Lista de IDs de mensagens

    Returns:
        Resumo do processamento
    """
    results = {
        'total': len(message_ids),
        'sent': 0,
        'failed': 0,
        'skipped': 0,
    }

    for message_id in message_ids:
        try:
            send_message_task.delay(message_id)
            results['sent'] += 1
        except Exception as e:
            logger.error(f"Erro ao enfileirar mensagem {message_id}: {e}")
            results['failed'] += 1

    logger.info(f"Batch de mensagens processado: {results}")
    return results


@shared_task(bind=True, base=TenantTask, queue='messages_low')
def retry_failed_messages(self, campaign_id: int) -> dict:
    """
    Reprocessa mensagens falhas de uma campanha.

    Args:
        campaign_id: ID da campanha

    Returns:
        Resumo do reprocessamento
    """
    from apps.messaging.models import Message

    failed_messages = Message.objects.filter(
        campaign_id=campaign_id,
        status=Message.Status.FAILED,
        retry_count__lt=3
    )

    results = {
        'total': failed_messages.count(),
        'requeued': 0,
        'skipped': 0,
    }

    for message in failed_messages:
        if message.can_retry:
            # Reseta status para pendente
            message.status = Message.Status.PENDING
            message.error_code = ''
            message.error_message = ''
            message.save(update_fields=['status', 'error_code', 'error_message', 'updated_at'])

            # Reenfileira
            send_message_task.delay(message.id)
            results['requeued'] += 1
        else:
            results['skipped'] += 1

    logger.info(f"Retry de mensagens da campanha {campaign_id}: {results}")
    return results
