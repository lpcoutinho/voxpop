"""
ViewSet for WhatsAppSession management.
"""
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.whatsapp.models import WhatsAppSession
from apps.whatsapp.api.serializers import (
    WhatsAppSessionSerializer,
    WhatsAppSessionListSerializer,
    WhatsAppSessionCreateSerializer,
    QRCodeSerializer,
)
from apps.whatsapp.services import WhatsAppService
from core.permissions import IsTenantMember, IsTenantAdmin
from core.pagination import StandardPagination
from core.exceptions import WhatsAppConnectionError


class WhatsAppSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing WhatsApp Sessions.

    list: GET /api/v1/whatsapp/sessions/
    create: POST /api/v1/whatsapp/sessions/
    retrieve: GET /api/v1/whatsapp/sessions/{id}/
    destroy: DELETE /api/v1/whatsapp/sessions/{id}/
    connect: POST /api/v1/whatsapp/sessions/{id}/connect/
    disconnect: POST /api/v1/whatsapp/sessions/{id}/disconnect/
    qrcode: GET /api/v1/whatsapp/sessions/{id}/qrcode/
    """
    permission_classes = [IsAuthenticated, IsTenantMember]
    pagination_class = StandardPagination
    http_method_names = ['get', 'post', 'patch', 'delete']  # No PUT

    def get_queryset(self):
        """Get active sessions."""
        return WhatsAppSession.objects.filter(is_active=True).order_by('-created_at')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return WhatsAppSessionListSerializer
        elif self.action in ['create', 'partial_update']:
            return WhatsAppSessionCreateSerializer
        elif self.action == 'qrcode':
            return QRCodeSerializer
        return WhatsAppSessionSerializer

    def get_permissions(self):
        """Require admin permission for create/delete."""
        if self.action in ['create', 'destroy']:
            return [IsAuthenticated(), IsTenantAdmin()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """
        Create a new WhatsApp session.
        Also creates the instance in Evolution API.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create session in database
        session = serializer.save()

        # Try to create instance in Evolution API
        try:
            service = WhatsAppService()
            result = service.create_instance_sync(session.instance_name)

            if result.get('success'):
                # Configure webhook URL
                webhook_url = f"{settings.BASE_URL}/api/v1/whatsapp/webhook/{session.instance_name}/"
                service.set_webhook_sync(session.instance_name, webhook_url)
                session.webhook_url = webhook_url
                session.save(update_fields=['webhook_url'])
        except Exception as e:
            # Log error but don't fail - session can be connected later
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to create Evolution API instance: {e}")

        return Response(
            WhatsAppSessionSerializer(session).data,
            status=status.HTTP_201_CREATED
        )

    def destroy(self, request, *args, **kwargs):
        """
        Delete a WhatsApp session.
        Check for active campaigns first.
        """
        session = self.get_object()

        # Check for active campaigns using this session
        if session.campaigns.filter(status__in=['scheduled', 'running']).exists():
            return Response(
                {'detail': 'Não é possível excluir uma sessão usada em campanhas ativas.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Try to delete from Evolution API
        try:
            service = WhatsAppService()
            service.delete_instance_sync(session.instance_name)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to delete Evolution API instance: {e}")

        # Soft delete by deactivating
        session.is_active = False
        session.save(update_fields=['is_active'])

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def connect(self, request, pk=None):
        """
        Start connection process for a session.
        POST /api/v1/whatsapp/sessions/{id}/connect/

        This will trigger QR code generation.
        """
        session = self.get_object()

        if session.status == WhatsAppSession.Status.CONNECTED:
            return Response(
                {'detail': 'Sessão já está conectada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = WhatsAppService()

            # Update status to connecting
            session.status = WhatsAppSession.Status.CONNECTING
            session.save(update_fields=['status'])

            # Request connection via get_qr_code_sync (calls /instance/connect endpoint)
            qr_code = service.get_qr_code_sync(session.instance_name)

            return Response({
                'detail': 'Conexão iniciada. Use o endpoint qrcode para obter o QR Code.',
                'status': session.status,
                'qr_code': qr_code if qr_code else None
            })

        except Exception as e:
            session.status = WhatsAppSession.Status.DISCONNECTED
            session.save(update_fields=['status'])
            raise WhatsAppConnectionError(f"Falha ao conectar: {str(e)}")

    @action(detail=True, methods=['post'])
    def disconnect(self, request, pk=None):
        """
        Disconnect a session.
        POST /api/v1/whatsapp/sessions/{id}/disconnect/
        """
        session = self.get_object()

        if session.status == WhatsAppSession.Status.DISCONNECTED:
            return Response(
                {'detail': 'Sessão já está desconectada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = WhatsAppService()
            service.disconnect_instance_sync(session.instance_name)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to disconnect Evolution API instance: {e}")

        # Update local status
        session.status = WhatsAppSession.Status.DISCONNECTED
        session.phone_number = ''
        session.save(update_fields=['status', 'phone_number'])

        return Response({
            'detail': 'Sessão desconectada com sucesso.',
            'status': session.status
        })

    @action(detail=True, methods=['get'])
    def qrcode(self, request, pk=None):
        """
        Get QR code for connection.
        GET /api/v1/whatsapp/sessions/{id}/qrcode/

        Returns the QR code if session is in connecting state.
        """
        session = self.get_object()

        if session.status == WhatsAppSession.Status.CONNECTED:
            return Response(
                {'detail': 'Sessão já está conectada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        qr_code = None
        # Try to get fresh QR code from Evolution API
        try:
            service = WhatsAppService()
            result = service.get_qr_code_sync(session.instance_name)

            if result.get('qrcode'):
                qr_code = result['qrcode']

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to get QR code: {e}")

        if not qr_code:
            return Response(
                {'detail': 'QR Code não disponível. Inicie a conexão primeiro.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Calculate expiration (QR codes typically expire in 60 seconds)
        expires_in = 60

        return Response({
            'qr_code': qr_code,
            'generated_at': timezone.now(),
            'expires_in_seconds': expires_in,
            'status': session.status
        })

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """
        Get current status of a session.
        GET /api/v1/whatsapp/sessions/{id}/status/

        Also refreshes status from Evolution API.
        """
        session = self.get_object()

        # Try to get status from Evolution API
        try:
            service = WhatsAppService()
            result = service.get_instance_status_sync(session.instance_name)

            # Update local status based on API response
            if result.get('state') == 'open':
                session.status = WhatsAppSession.Status.CONNECTED
                if result.get('phone'):
                    session.phone_number = result['phone']
            elif result.get('state') == 'connecting':
                session.status = WhatsAppSession.Status.CONNECTING
            else:
                session.status = WhatsAppSession.Status.DISCONNECTED

            session.last_health_check = timezone.now()
            session.is_healthy = True
            session.save(update_fields=['status', 'phone_number', 'last_health_check', 'is_healthy'])

        except Exception as e:
            session.is_healthy = False
            session.save(update_fields=['is_healthy'])

        return Response(WhatsAppSessionSerializer(session).data)
