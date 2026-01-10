"""
Serializers for MessageTemplate model.
"""
from rest_framework import serializers

from apps.messaging.models import MessageTemplate


class MessageTemplateSerializer(serializers.ModelSerializer):
    """Full serializer for message template detail view."""
    has_media = serializers.BooleanField(read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = MessageTemplate
        fields = [
            'id', 'name', 'description', 'message_type', 'content',
            'media_url', 'media_filename', 'media_mimetype',
            'variables', 'has_media', 'is_active',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'variables']

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name()
        return None


class MessageTemplateListSerializer(serializers.ModelSerializer):
    """Simplified serializer for template list view."""
    has_media = serializers.BooleanField(read_only=True)

    class Meta:
        model = MessageTemplate
        fields = [
            'id', 'name', 'message_type', 'has_media',
            'is_active', 'created_at'
        ]


class MessageTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating templates."""

    class Meta:
        model = MessageTemplate
        fields = [
            'name', 'description', 'message_type', 'content',
            'media_url', 'media_filename', 'media_mimetype', 'is_active'
        ]

    def validate(self, attrs):
        """Validate template data."""
        message_type = attrs.get('message_type', MessageTemplate.Type.TEXT)
        media_url = attrs.get('media_url', '')

        # If not text type, media_url is required
        if message_type != MessageTemplate.Type.TEXT and not media_url:
            raise serializers.ValidationError({
                'media_url': 'URL da mídia é obrigatória para este tipo de mensagem.'
            })

        return attrs

    def create(self, validated_data):
        """Create template and extract variables."""
        validated_data['created_by'] = self.context['request'].user
        template = super().create(validated_data)

        # Auto-extract variables from content
        template.extract_variables()
        template.save(update_fields=['variables'])

        return template

    def update(self, instance, validated_data):
        """Update template and re-extract variables if content changed."""
        instance = super().update(instance, validated_data)

        # Re-extract variables if content was updated
        if 'content' in validated_data:
            instance.extract_variables()
            instance.save(update_fields=['variables'])

        return instance


class TemplatePreviewSerializer(serializers.Serializer):
    """Input serializer for template preview."""
    context = serializers.DictField(
        required=False,
        default=dict,
        help_text="Variables to render in template. Ex: {'name': 'João', 'city': 'SP'}"
    )


class TemplatePreviewResponseSerializer(serializers.Serializer):
    """Response serializer for template preview."""
    rendered_content = serializers.CharField()
    variables_used = serializers.ListField(child=serializers.CharField())
    missing_variables = serializers.ListField(child=serializers.CharField())
