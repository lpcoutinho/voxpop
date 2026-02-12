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

    # Extrai informações do payload
    key = payload.get('key', {})
    message_id = key.get('id', '')
    status = payload.get('status', '').lower()

    if not message_id:
        return

    # Busca mensagem pelo ID externo
    try:
        message = Message.objects.get(whatsapp_message_id=message_id)
    except Message.DoesNotExist:
        # Tenta pelo external_id
        try:
            message = Message.objects.get(external_id=message_id)
        except Message.DoesNotExist:
            logger.warning(f"Mensagem não encontrada: {message_id}")
            return

    # Atualiza status
    if status in ['delivered', 'delivery_ack', 'server_ack']:
        message.mark_as_delivered()
        logger.info(f"Mensagem {message.id} marcada como entregue")

    elif status in ['read', 'played']:
        message.mark_as_read()
        logger.info(f"Mensagem {message.id} marcada como lida")

    elif status in ['error', 'failed']:
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
