import os
import uuid

from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, status, decorators
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.campaigns.models import Campaign
from apps.campaigns.api.serializers import (
    CampaignListSerializer,
    CampaignDetailSerializer,
    CampaignCreateSerializer
)
from apps.campaigns.services.campaign_service import campaign_service
import logging

logger = logging.getLogger(__name__)

ALLOWED_MEDIA_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'mp4', 'pdf'}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

class CampaignViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filtra campanhas do tenant atual (já tratado pelo middleware + django-tenants)
        return Campaign.objects.all().select_related(
            'whatsapp_session', 'created_by', 'target_segment'
        ).prefetch_related('target_tags', 'items')

    def get_serializer_class(self):
        if self.action == 'list':
            return CampaignListSerializer
        if self.action == 'create':
            return CampaignCreateSerializer
        return CampaignDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @decorators.action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Inicia o processamento da campanha."""
        campaign = self.get_object()
        
        if campaign.status not in [Campaign.Status.DRAFT, Campaign.Status.PAUSED, Campaign.Status.FAILED]:
            return Response(
                {"detail": "Campanha não pode ser iniciada neste estado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Chama o serviço para iniciar (popula itens e enfileira)
            campaign_service.start_campaign(campaign)
            return Response({"detail": "Campanha iniciada com sucesso."})
        except Exception as e:
            logger.error(f"Erro ao iniciar campanha {campaign.id}: {str(e)}", exc_info=True)
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @decorators.action(
        detail=False,
        methods=['post'],
        url_path='upload-media',
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_media(self, request):
        """Faz upload de mídia para uso em campanhas."""
        file = request.FILES.get('file')
        if not file:
            return Response(
                {"detail": "Nenhum arquivo enviado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar tamanho
        if file.size > MAX_UPLOAD_SIZE:
            return Response(
                {"detail": "Arquivo muito grande. Tamanho máximo: 10MB."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar extensão
        ext = file.name.rsplit('.', 1)[-1].lower() if '.' in file.name else ''
        if ext not in ALLOWED_MEDIA_EXTENSIONS:
            return Response(
                {"detail": f"Extensão não permitida. Permitidas: {', '.join(ALLOWED_MEDIA_EXTENSIONS)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Determinar media_type
        if ext in ('jpg', 'jpeg', 'png', 'gif'):
            media_type = 'image'
        elif ext == 'mp4':
            media_type = 'video'
        elif ext == 'pdf':
            media_type = 'document'
        else:
            media_type = 'image'

        # Salvar arquivo
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'campaigns')
        os.makedirs(upload_dir, exist_ok=True)

        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(upload_dir, filename)

        with open(filepath, 'wb+') as dest:
            for chunk in file.chunks():
                dest.write(chunk)

        media_url = request.build_absolute_uri(f'{settings.MEDIA_URL}campaigns/{filename}')

        return Response({
            "media_url": media_url,
            "media_type": media_type,
            "filename": file.name,
        })

    @decorators.action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pausa o envio da campanha."""
        campaign = self.get_object()
        if campaign.status != Campaign.Status.RUNNING:
            return Response(
                {"detail": "Apenas campanhas em andamento podem ser pausadas."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        campaign.status = Campaign.Status.PAUSED
        campaign.save()
        return Response({"detail": "Campanha pausada."})
