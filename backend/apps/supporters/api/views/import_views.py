"""
ViewSet for Import Job management.
"""
import os
import uuid

from django.conf import settings
from rest_framework import viewsets, status, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from apps.supporters.models import ImportJob
from apps.supporters.api.serializers import (
    ImportJobSerializer,
    ImportJobCreateSerializer,
    ImportJobStatusSerializer,
)
from core.permissions import IsTenantMember, IsTenantAdmin


class ImportViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet for managing Import Jobs.

    list: GET /api/v1/supporters/import/
    create: POST /api/v1/supporters/import/
    retrieve: GET /api/v1/supporters/import/{id}/
    """
    permission_classes = [IsAuthenticated, IsTenantMember]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        """Get import jobs ordered by creation date."""
        return ImportJob.objects.select_related('created_by').order_by('-created_at')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ImportJobCreateSerializer
        elif self.action == 'retrieve':
            return ImportJobStatusSerializer
        return ImportJobSerializer

    def get_permissions(self):
        """Require admin permission to create imports."""
        if self.action == 'create':
            return [IsAuthenticated(), IsTenantAdmin()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """
        Create a new import job.
        POST /api/v1/supporters/import/

        The file is saved and a background task is triggered.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get validated data
        file = serializer.validated_data['file']
        column_mapping = serializer.validated_data.get('column_mapping', {})
        auto_tag_ids = serializer.validated_data.get('auto_tag_ids', [])

        # Generate unique filename
        ext = file.name.split('.')[-1]
        unique_name = f"{uuid.uuid4().hex}.{ext}"

        # Ensure upload directory exists
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'imports')
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, unique_name)

        # Save file
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Create import job
        import_job = ImportJob.objects.create(
            file_name=file.name,
            file_path=file_path,
            column_mapping=column_mapping,
            created_by=request.user,
            status=ImportJob.Status.PENDING
        )

        # Add auto tags
        if auto_tag_ids:
            import_job.auto_tags.set(auto_tag_ids)

        # Trigger async processing task
        from apps.supporters.tasks import process_import_job
        process_import_job.delay(import_job.id)

        return Response(
            ImportJobSerializer(import_job).data,
            status=status.HTTP_202_ACCEPTED
        )
