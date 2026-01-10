"""
Webhook endpoint for Evolution API callbacks.
"""
import logging
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.whatsapp.models import WhatsAppSession, WebhookLog

logger = logging.getLogger(__name__)


class WebhookView(APIView):
    """
    Public endpoint to receive webhooks from Evolution API.

    POST /api/v1/whatsapp/webhook/{instance_name}/

    This endpoint is called by Evolution API to notify about:
    - QR code updates
    - Connection status changes
    - Message delivery status updates
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # No auth for webhooks

    def post(self, request, instance_name):
        """
        Receive and process webhook from Evolution API.
        """
        # Find session by instance name
        session = get_object_or_404(
            WhatsAppSession,
            instance_name=instance_name,
            is_active=True
        )

        # Extract event type from payload
        event_type = request.data.get('event', 'unknown')

        logger.info(f"Webhook received: {event_type} for {instance_name}")

        # Create webhook log
        webhook_log = WebhookLog.objects.create(
            session=session,
            event_type=event_type,
            payload=request.data
        )

        # Process certain events synchronously for immediate updates
        try:
            self._process_event_sync(session, event_type, request.data)
        except Exception as e:
            logger.exception(f"Error processing webhook sync: {e}")

        # Queue async processing for heavy operations
        from apps.whatsapp.tasks import process_webhook
        process_webhook.delay(webhook_log.id)

        return Response({'status': 'received'}, status=202)

    def _process_event_sync(self, session, event_type, payload):
        """
        Process certain events synchronously for immediate UI updates.
        """
        if event_type == 'qrcode.updated':
            # Update status only
            session.status = WhatsAppSession.Status.CONNECTING
            session.save(update_fields=['status'])

        elif event_type == 'connection.update':
            # Update connection status
            state = payload.get('data', {}).get('state')

            if state == 'open':
                session.status = WhatsAppSession.Status.CONNECTED
                # Try to get phone number
                phone = payload.get('data', {}).get('connection', {}).get('wid', {}).get('user')
                if phone:
                    session.phone_number = f"+{phone}"
                session.save(update_fields=['status', 'phone_number'])
                logger.info(f"Session {session.name} connected: {session.phone_number}")

            elif state == 'close':
                session.status = WhatsAppSession.Status.DISCONNECTED
                session.phone_number = ''
                session.save(update_fields=['status', 'phone_number'])
                logger.info(f"Session {session.name} disconnected")

            elif state == 'connecting':
                session.status = WhatsAppSession.Status.CONNECTING
                session.save(update_fields=['status'])

        elif event_type == 'messages.update':
            # Message status updates are processed async
            pass

        elif event_type == 'send.message':
            # Message sent confirmation - processed async
            pass
