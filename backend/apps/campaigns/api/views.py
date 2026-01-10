from rest_framework import viewsets, status, decorators
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from apps.campaigns.models import Campaign
from apps.campaigns.api.serializers import (
    CampaignListSerializer, 
    CampaignDetailSerializer, 
    CampaignCreateSerializer
)
from apps.campaigns.services.campaign_service import campaign_service
import logging

logger = logging.getLogger(__name__)

class CampaignViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filtra campanhas do tenant atual (já tratado pelo middleware + django-tenants)
        return Campaign.objects.all().select_related(
            'whatsapp_session', 'created_by', 'target_segment'
        ).prefetch_related('target_tags')

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
