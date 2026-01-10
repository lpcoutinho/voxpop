"""
ViewSet for Segment management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.supporters.models import Segment
from apps.supporters.api.serializers import (
    SegmentSerializer,
    SegmentListSerializer,
    SegmentCreateSerializer,
    SegmentPreviewSerializer,
    SupporterListSerializer,
)
from core.permissions import IsTenantMember
from core.pagination import StandardPagination


class SegmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Segments.

    list: GET /api/v1/supporters/segments/
    create: POST /api/v1/supporters/segments/
    retrieve: GET /api/v1/supporters/segments/{id}/
    update: PUT /api/v1/supporters/segments/{id}/
    partial_update: PATCH /api/v1/supporters/segments/{id}/
    destroy: DELETE /api/v1/supporters/segments/{id}/
    preview: GET /api/v1/supporters/segments/{id}/preview/
    """
    permission_classes = [IsAuthenticated, IsTenantMember]
    pagination_class = StandardPagination

    def get_queryset(self):
        """Get segments ordered by name."""
        return Segment.objects.select_related('created_by').order_by('name')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return SegmentListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return SegmentCreateSerializer
        return SegmentSerializer

    def destroy(self, request, *args, **kwargs):
        """
        Delete a segment.
        Check if it's used in any active campaign first.
        """
        instance = self.get_object()

        # Check if segment is used in any active campaign
        if instance.campaigns.filter(
            status__in=['scheduled', 'running']
        ).exists():
            return Response(
                {'detail': 'Não é possível excluir um segmento usado em campanhas ativas.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """
        Preview supporters that match the segment filters.
        GET /api/v1/supporters/segments/{id}/preview/

        Returns count and a sample of 10 supporters.
        """
        segment = self.get_object()

        # Get matching supporters
        queryset = segment.get_supporters_queryset()

        # Get count and sample
        count = queryset.count()
        sample = list(queryset.prefetch_related('tags')[:10])

        # Update cached count
        segment.cached_count = count
        segment.save(update_fields=['cached_count', 'cached_at'])

        return Response({
            'count': count,
            'sample': SupporterListSerializer(sample, many=True).data
        })

    @action(detail=False, methods=['post'], url_path='preview')
    def preview_filters(self, request):
        """
        Preview supporters for given filters without creating a segment.
        POST /api/v1/supporters/segments/preview/
        Body: {"filters": {...}}

        Useful for the segment builder UI to show live preview.
        """
        filters = request.data.get('filters', {})

        if not filters:
            return Response(
                {'detail': 'Informe os filtros para preview.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create a temporary segment instance (not saved)
        temp_segment = Segment(filters=filters)

        try:
            queryset = temp_segment.get_supporters_queryset()
            count = queryset.count()
            sample = list(queryset.prefetch_related('tags')[:10])

            return Response({
                'count': count,
                'sample': SupporterListSerializer(sample, many=True).data
            })
        except Exception as e:
            return Response(
                {'detail': f'Erro ao aplicar filtros: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
