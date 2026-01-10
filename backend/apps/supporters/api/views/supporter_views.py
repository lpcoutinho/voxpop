"""
ViewSet for Supporter management.
"""
import logging
from django.db.models import Prefetch
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

logger = logging.getLogger(__name__)

from apps.supporters.models import Supporter, Tag, SupporterTag
from apps.supporters.api.serializers import (
    SupporterListSerializer,
    SupporterDetailSerializer,
    SupporterCreateSerializer,
    SupporterUpdateSerializer,
    SupporterTagsSerializer,
    SupporterBulkActionSerializer,
)
from apps.supporters.api.filters import SupporterFilter
from core.permissions import IsTenantMember
from core.pagination import StandardPagination


class SupporterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Supporters.

    list: GET /api/v1/supporters/
    create: POST /api/v1/supporters/
    retrieve: GET /api/v1/supporters/{id}/
    update: PUT /api/v1/supporters/{id}/
    partial_update: PATCH /api/v1/supporters/{id}/
    destroy: DELETE /api/v1/supporters/{id}/
    add_tags: POST /api/v1/supporters/{id}/tags/
    remove_tags: DELETE /api/v1/supporters/{id}/tags/
    """
    permission_classes = [IsAuthenticated, IsTenantMember]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = SupporterFilter
    search_fields = ['name', 'phone', 'email']
    ordering_fields = ['name', 'created_at', 'city']
    ordering = ['-created_at']

    def get_queryset(self):
        """Get active supporters with prefetched tags (SoftDeleteManager already filters deleted)."""
        return Supporter.objects.prefetch_related(
            Prefetch(
                'tags',
                queryset=Tag.objects.filter(is_active=True)
            )
        )

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return SupporterListSerializer
        elif self.action == 'create':
            return SupporterCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SupporterUpdateSerializer
        elif self.action in ['add_tags', 'remove_tags']:
            return SupporterTagsSerializer
        elif self.action in ['bulk_promote', 'bulk_demote', 'bulk_blacklist', 'bulk_unblacklist']:
            return SupporterBulkActionSerializer
        return SupporterDetailSerializer

    def perform_destroy(self, instance):
        """Soft delete the supporter."""
        instance.delete()  # Uses SoftDeleteModel.delete() which sets deleted_at

    def update(self, request, *args, **kwargs):
        """Override to log validation errors."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if not serializer.is_valid():
            logger.warning(
                f"Supporter update validation failed for ID {instance.id}. "
                f"Data: {request.data}. Errors: {serializer.errors}"
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='tags')
    def add_tags(self, request, pk=None):
        """
        Add tags to a supporter.
        POST /api/v1/supporters/{id}/tags/
        Body: {"tag_ids": [1, 2, 3]}
        """
        supporter = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tag_ids = serializer.validated_data['tag_ids']
        added = 0

        for tag_id in tag_ids:
            _, created = SupporterTag.objects.get_or_create(
                supporter=supporter,
                tag_id=tag_id
            )
            if created:
                added += 1

        return Response({
            'detail': f'{added} tag(s) adicionada(s) com sucesso.',
            'tags_added': added
        })

    @add_tags.mapping.delete
    def remove_tags(self, request, pk=None):
        """
        Remove tags from a supporter.
        DELETE /api/v1/supporters/{id}/tags/
        Body: {"tag_ids": [1, 2, 3]}
        """
        supporter = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tag_ids = serializer.validated_data['tag_ids']
        deleted, _ = SupporterTag.objects.filter(
            supporter=supporter,
            tag_id__in=tag_ids
        ).delete()

        return Response({
            'detail': f'{deleted} tag(s) removida(s) com sucesso.',
            'tags_removed': deleted
        })

    # ===========================================
    # Status Change Actions (Individual)
    # ===========================================

    @action(detail=True, methods=['post'], url_path='promote')
    def promote(self, request, pk=None):
        """
        Promote a single contact from Lead to Supporter.
        POST /api/v1/supporters/{id}/promote/
        """
        supporter = self.get_object()

        if supporter.is_supporter_status:
            return Response(
                {'detail': 'Este contato já é um Apoiador.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        success = supporter.promote_to_supporter()

        if success:
            return Response({
                'detail': f'{supporter.name} promovido para Apoiador com sucesso.',
                'contact_status': supporter.contact_status
            })
        else:
            return Response(
                {'detail': 'Erro ao promover contato. Tags de sistema não encontradas.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='demote')
    def demote(self, request, pk=None):
        """
        Demote a single contact from Supporter to Lead.
        POST /api/v1/supporters/{id}/demote/
        """
        supporter = self.get_object()

        if supporter.is_lead:
            return Response(
                {'detail': 'Este contato já é um Lead.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        success = supporter.demote_to_lead()

        if success:
            return Response({
                'detail': f'{supporter.name} movido para Lead com sucesso.',
                'contact_status': supporter.contact_status
            })
        else:
            return Response(
                {'detail': 'Erro ao mover contato. Tags de sistema não encontradas.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='blacklist')
    def blacklist(self, request, pk=None):
        """
        Add a single contact to blacklist.
        POST /api/v1/supporters/{id}/blacklist/
        """
        supporter = self.get_object()

        if supporter.is_blacklisted:
            return Response(
                {'detail': 'Este contato já está na Blacklist.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        success = supporter.add_to_blacklist()

        if success:
            return Response({
                'detail': f'{supporter.name} adicionado à Blacklist.',
                'contact_status': supporter.contact_status
            })
        else:
            return Response(
                {'detail': 'Erro ao adicionar à blacklist. Tag de sistema não encontrada.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='unblacklist')
    def unblacklist(self, request, pk=None):
        """
        Remove a single contact from blacklist.
        POST /api/v1/supporters/{id}/unblacklist/
        """
        supporter = self.get_object()

        if not supporter.is_blacklisted:
            return Response(
                {'detail': 'Este contato não está na Blacklist.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        success = supporter.remove_from_blacklist()

        if success:
            return Response({
                'detail': f'{supporter.name} removido da Blacklist.',
                'contact_status': supporter.contact_status
            })
        else:
            return Response(
                {'detail': 'Erro ao remover da blacklist.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ===========================================
    # Bulk Status Change Actions
    # ===========================================

    @action(detail=False, methods=['post'], url_path='bulk-promote')
    def bulk_promote(self, request):
        """
        Promote multiple contacts from Lead to Supporter.
        POST /api/v1/supporters/bulk-promote/
        Body: {"supporter_ids": [1, 2, 3]}
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        supporter_ids = serializer.validated_data['supporter_ids']
        supporters = Supporter.objects.filter(id__in=supporter_ids)

        updated = 0
        for supporter in supporters:
            if supporter.promote_to_supporter():
                updated += 1

        return Response({
            'success': True,
            'message': f'{updated} contato(s) promovido(s) para Apoiador.',
            'updated_count': updated
        })

    @action(detail=False, methods=['post'], url_path='bulk-demote')
    def bulk_demote(self, request):
        """
        Demote multiple contacts from Supporter to Lead.
        POST /api/v1/supporters/bulk-demote/
        Body: {"supporter_ids": [1, 2, 3]}
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        supporter_ids = serializer.validated_data['supporter_ids']
        supporters = Supporter.objects.filter(id__in=supporter_ids)

        updated = 0
        for supporter in supporters:
            if supporter.demote_to_lead():
                updated += 1

        return Response({
            'success': True,
            'message': f'{updated} contato(s) movido(s) para Lead.',
            'updated_count': updated
        })

    @action(detail=False, methods=['post'], url_path='bulk-blacklist')
    def bulk_blacklist(self, request):
        """
        Add multiple contacts to blacklist.
        POST /api/v1/supporters/bulk-blacklist/
        Body: {"supporter_ids": [1, 2, 3]}
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        supporter_ids = serializer.validated_data['supporter_ids']
        supporters = Supporter.objects.filter(id__in=supporter_ids)

        updated = 0
        for supporter in supporters:
            if supporter.add_to_blacklist():
                updated += 1

        return Response({
            'success': True,
            'message': f'{updated} contato(s) adicionado(s) à Blacklist.',
            'updated_count': updated
        })

    @action(detail=False, methods=['post'], url_path='bulk-unblacklist')
    def bulk_unblacklist(self, request):
        """
        Remove multiple contacts from blacklist.
        POST /api/v1/supporters/bulk-unblacklist/
        Body: {"supporter_ids": [1, 2, 3]}
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        supporter_ids = serializer.validated_data['supporter_ids']
        supporters = Supporter.objects.filter(id__in=supporter_ids)

        updated = 0
        for supporter in supporters:
            if supporter.remove_from_blacklist():
                updated += 1

        return Response({
            'success': True,
            'message': f'{updated} contato(s) removido(s) da Blacklist.',
            'updated_count': updated
        })
