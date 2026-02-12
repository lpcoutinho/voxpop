"""
Tasks para processamento de webhooks do WhatsApp.
"""
import logging
from celery import shared_task
from django.utils import timezone

from apps.whatsapp.models import WebhookLog
from apps.whatsapp.handlers.message_received_handler import MessageReceivedHandler
from apps.whatsapp.handlers.message_status_handler import MessageStatusHandler

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='whatsapp.process_webhook')
def process_webhook(self, webhook_log_id: int):
    """
    Processa webhook recebido da Evolution API.

    Args:
        webhook_log_id: ID do WebhookLog a ser processado
    """
    try:
        # Busca o log do webhook
        webhook_log = WebhookLog.objects.select_related('session').get(id=webhook_log_id)

        logger.info(
            f"Processing webhook {webhook_log.event_type} "
            f"for instance {webhook_log.session.instance_name}"
        )

        # Processa baseado no tipo de evento
        event_type = webhook_log.event_type
        payload = webhook_log.payload

        if event_type == 'messages.upsert':
            # Nova mensagem recebida
            handler = MessageReceivedHandler()
            result = handler._process_message_upsert(
                session=webhook_log.session,
                payload=payload
            )
            logger.info(f"Message upsert processed: {result}")

        elif event_type == 'messages.update':
            # Atualização de status de mensagem
            logger.info(f"🔔 Iniciando processamento MESSAGES.UPDATE")
            logger.info(f"   Payload: {payload}")

            handler = MessageStatusHandler()
            result = handler._process_message_update(
                session=webhook_log.session,
                payload=payload
            )
            logger.info(f"Message update processed: {result}")

        elif event_type == 'send.message':
            # Confirmação de envio
            logger.info(f"Message sent confirmation: {payload}")
            # Atualiza status da mensagem para 'sent'
            # TODO: Implementar lógica de atualização

        elif event_type == 'status.instance':
            # Status da instância
            logger.info(f"Instance status: {payload}")
            # Atualiza status da sessão se necessário
            # TODO: Implementar lógica de atualização

        else:
            logger.warning(f"Unhandled event type: {event_type}")

        # Marca como processado
        webhook_log.processed_at = timezone.now()
        webhook_log.status = 'processed'
        webhook_log.save(update_fields=['processed_at', 'status'])

    except WebhookLog.DoesNotExist:
        logger.error(f"WebhookLog {webhook_log_id} not found")

    except Exception as e:
        logger.exception(f"Error processing webhook {webhook_log_id}: {e}")

        # Marca como falha se possível
        try:
            webhook_log.status = 'failed'
            webhook_log.error_message = str(e)
            webhook_log.save(update_fields=['status', 'error_message'])
        except:
            pass

        # Re-raise para retry do Celery
        raise
