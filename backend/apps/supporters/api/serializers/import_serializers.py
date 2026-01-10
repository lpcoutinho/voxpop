"""
Serializers for ImportJob model.
"""
from rest_framework import serializers

from apps.supporters.models import ImportJob, Tag


class ImportJobSerializer(serializers.ModelSerializer):
    """Full import job serializer."""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    progress_percentage = serializers.FloatField(read_only=True)
    duration_seconds = serializers.IntegerField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)

    class Meta:
        model = ImportJob
        fields = [
            'id', 'file_name', 'status',
            'total_rows', 'processed_rows', 'success_count',
            'error_count', 'skipped_count', 'errors_log',
            'column_mapping', 'progress_percentage', 'duration_seconds',
            'is_completed', 'created_by', 'created_by_name',
            'started_at', 'completed_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'status', 'total_rows', 'processed_rows',
            'success_count', 'error_count', 'skipped_count',
            'errors_log', 'created_by', 'started_at', 'completed_at', 'created_at'
        ]


class ImportJobCreateSerializer(serializers.Serializer):
    """Serializer for creating an import job."""
    file = serializers.FileField()
    column_mapping = serializers.DictField(required=False, default=dict)
    auto_tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list
    )

    def validate_file(self, value):
        """Validate uploaded file."""
        # Check file extension
        allowed_extensions = ['.csv', '.xlsx', '.xls']
        ext = '.' + value.name.split('.')[-1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"Formato não suportado. Use: {', '.join(allowed_extensions)}"
            )

        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("Arquivo muito grande. Máximo: 10MB")

        return value

    def validate_column_mapping(self, value):
        """Validate column mapping structure."""
        valid_fields = {
            'name', 'phone', 'email', 'cpf',
            'city', 'neighborhood', 'state', 'zip_code',
            'electoral_zone', 'electoral_section',
            'birth_date', 'gender'
        }

        # Keys are CSV column names, values are model field names
        for csv_col, model_field in value.items():
            if model_field not in valid_fields:
                raise serializers.ValidationError(
                    f"Campo '{model_field}' não é válido. "
                    f"Campos válidos: {valid_fields}"
                )

        return value

    def validate_auto_tag_ids(self, value):
        """Validate tag IDs exist."""
        if value:
            existing_ids = set(
                Tag.objects.filter(id__in=value, is_active=True)
                .values_list('id', flat=True)
            )
            invalid_ids = set(value) - existing_ids
            if invalid_ids:
                raise serializers.ValidationError(f"Tags não encontradas: {invalid_ids}")
        return value


class ImportJobStatusSerializer(serializers.ModelSerializer):
    """Minimal serializer for checking import job status."""
    progress_percentage = serializers.FloatField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)

    class Meta:
        model = ImportJob
        fields = [
            'id', 'status', 'total_rows', 'processed_rows',
            'success_count', 'error_count', 'skipped_count',
            'progress_percentage', 'is_completed', 'errors_log'
        ]
