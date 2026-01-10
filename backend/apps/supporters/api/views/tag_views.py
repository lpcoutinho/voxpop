"""
ViewSet for Tag management.
"""
from django.db.models import Count
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.supporters.models import Tag
from apps.supporters.api.serializers import (
    TagSerializer,
    TagListSerializer,
    TagCreateSerializer,
)
from core.permissions import IsTenantMember
from core.pagination import StandardPagination


class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Tags.

    list: GET /api/v1/supporters/tags/
    create: POST /api/v1/supporters/tags/
    retrieve: GET /api/v1/supporters/tags/{id}/
    update: PUT /api/v1/supporters/tags/{id}/
    partial_update: PATCH /api/v1/supporters/tags/{id}/
    destroy: DELETE /api/v1/supporters/tags/{id}/
    """
    permission_classes = [IsAuthenticated, IsTenantMember]
    pagination_class = StandardPagination

    def get_queryset(self):
        """Get tags with supporter count annotation."""
        # Use _count suffix to avoid conflict with model property
        return Tag.objects.annotate(
            _supporters_count=Count('supporter_tags')
        ).order_by('name')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return TagListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TagCreateSerializer
        return TagSerializer

    def destroy(self, request, *args, **kwargs):
        """
        Delete a tag.
        This will also remove the tag from all supporters.
        """
        instance = self.get_object()

        # Check if tag is used in any campaign
        if instance.campaigns.filter(
            status__in=['scheduled', 'running']
        ).exists():
            return Response(
                {'detail': 'Não é possível excluir uma tag usada em campanhas ativas.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Delete tag (cascade will remove SupporterTag entries)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
