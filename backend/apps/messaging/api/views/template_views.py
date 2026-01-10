"""
ViewSet for MessageTemplate management.
"""
import re
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.messaging.models import MessageTemplate
from apps.messaging.api.serializers import (
    MessageTemplateSerializer,
    MessageTemplateListSerializer,
    MessageTemplateCreateSerializer,
    TemplatePreviewSerializer,
)
from core.permissions import IsTenantMember
from core.pagination import StandardPagination


class MessageTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Message Templates.

    list: GET /api/v1/messages/templates/
    create: POST /api/v1/messages/templates/
    retrieve: GET /api/v1/messages/templates/{id}/
    update: PUT /api/v1/messages/templates/{id}/
    partial_update: PATCH /api/v1/messages/templates/{id}/
    destroy: DELETE /api/v1/messages/templates/{id}/
    preview: POST /api/v1/messages/templates/{id}/preview/
    """
    permission_classes = [IsAuthenticated, IsTenantMember]
    pagination_class = StandardPagination

    def get_queryset(self):
        """Get active templates (soft-deleted are automatically excluded by manager)."""
        return MessageTemplate.objects.select_related('created_by').order_by('-created_at')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return MessageTemplateListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return MessageTemplateCreateSerializer
        elif self.action == 'preview':
            return TemplatePreviewSerializer
        return MessageTemplateSerializer

    def perform_destroy(self, instance):
        """Soft delete the template (using the model's delete method which does soft delete)."""
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        """
        Delete a template.
        Check if it's used in any active campaign first.
        """
        instance = self.get_object()

        # Check if template is used in any active campaign
        if instance.campaigns.filter(
            status__in=['scheduled', 'running']
        ).exists():
            return Response(
                {'detail': 'Não é possível excluir um template usado em campanhas ativas.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """
        Preview a template with given context variables.
        POST /api/v1/messages/templates/{id}/preview/
        Body: {"context": {"name": "João", "city": "São Paulo"}}
        """
        template = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        context = serializer.validated_data.get('context', {})

        # Render template
        rendered_content = template.render(context)

        # Find which variables were used
        variables_used = []
        missing_variables = []

        for var in template.variables:
            if var in context:
                variables_used.append(var)
            else:
                missing_variables.append(var)

        return Response({
            'rendered_content': rendered_content,
            'variables_used': variables_used,
            'missing_variables': missing_variables
        })

    @action(detail=True, methods=['post'], url_path='duplicate')
    def duplicate(self, request, pk=None):
        """
        Duplicate a template.
        POST /api/v1/messages/templates/{id}/duplicate/
        """
        template = self.get_object()

        # Create a copy
        new_template = MessageTemplate.objects.create(
            name=f"{template.name} (Cópia)",
            description=template.description,
            message_type=template.message_type,
            content=template.content,
            media_url=template.media_url,
            media_filename=template.media_filename,
            media_mimetype=template.media_mimetype,
            variables=template.variables,
            is_active=False,  # New copy starts inactive
            created_by=request.user
        )

        return Response(
            MessageTemplateSerializer(new_template).data,
            status=status.HTTP_201_CREATED
        )
