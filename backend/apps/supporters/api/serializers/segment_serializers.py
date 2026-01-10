"""
Serializers for Segment model.
"""
from rest_framework import serializers

from apps.supporters.models import Segment
from apps.supporters.api.serializers.supporter_serializers import SupporterListSerializer


class SegmentSerializer(serializers.ModelSerializer):
    """Full segment serializer."""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    leads_count = serializers.SerializerMethodField()
    supporters_count = serializers.SerializerMethodField()

    class Meta:
        model = Segment
        fields = [
            'id', 'name', 'description', 'filters',
            'cached_count', 'cached_at', 'is_active',
            'leads_count', 'supporters_count',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'cached_count', 'cached_at', 'created_by', 'created_at', 'updated_at']

    def get_leads_count(self, obj):
        """Count leads in this segment."""
        from apps.supporters.models import Tag
        try:
            lead_tag = Tag.objects.get(name='Lead', is_system=True)
            return obj.get_supporters_queryset().filter(tags=lead_tag).count()
        except Tag.DoesNotExist:
            return 0

    def get_supporters_count(self, obj):
        """Count supporters (apoiadores) in this segment."""
        from apps.supporters.models import Tag
        try:
            supporter_tag = Tag.objects.get(name='Apoiador', is_system=True)
            return obj.get_supporters_queryset().filter(tags=supporter_tag).count()
        except Tag.DoesNotExist:
            return 0


class SegmentListSerializer(serializers.ModelSerializer):
    """Simplified segment for list view."""
    leads_count = serializers.SerializerMethodField()
    supporters_count = serializers.SerializerMethodField()

    class Meta:
        model = Segment
        fields = ['id', 'name', 'cached_count', 'leads_count', 'supporters_count', 'is_active', 'created_at']

    def get_leads_count(self, obj):
        """Count leads in this segment."""
        from apps.supporters.models import Tag
        try:
            lead_tag = Tag.objects.get(name='Lead', is_system=True)
            return obj.get_supporters_queryset().filter(tags=lead_tag).count()
        except Tag.DoesNotExist:
            return 0

    def get_supporters_count(self, obj):
        """Count supporters (apoiadores) in this segment."""
        from apps.supporters.models import Tag
        try:
            supporter_tag = Tag.objects.get(name='Apoiador', is_system=True)
            return obj.get_supporters_queryset().filter(tags=supporter_tag).count()
        except Tag.DoesNotExist:
            return 0


class SegmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating segments."""

    class Meta:
        model = Segment
        fields = ['name', 'description', 'filters', 'is_active']

    def validate_filters(self, value):
        """Validate filters structure."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Filters deve ser um objeto JSON.")

        valid_keys = {
            'contact_status',
            'city', 'state', 'neighborhood', 'gender',
            'tags', 'tags_all', 'age_min', 'age_max',
            'electoral_zone', 'electoral_section', 'source',
            'whatsapp_opt_in'
        }

        invalid_keys = set(value.keys()) - valid_keys
        if invalid_keys:
            raise serializers.ValidationError(
                f"Campos de filtro inválidos: {invalid_keys}. "
                f"Campos válidos: {valid_keys}"
            )

        # Validate age values
        if 'age_min' in value and not isinstance(value['age_min'], int):
            raise serializers.ValidationError("age_min deve ser um número inteiro.")
        if 'age_max' in value and not isinstance(value['age_max'], int):
            raise serializers.ValidationError("age_max deve ser um número inteiro.")
        if 'age_min' in value and 'age_max' in value:
            if value['age_min'] > value['age_max']:
                raise serializers.ValidationError("age_min não pode ser maior que age_max.")

        # Validate tags is a list
        if 'tags' in value and not isinstance(value['tags'], list):
            raise serializers.ValidationError("tags deve ser uma lista de IDs.")
        if 'tags_all' in value and not isinstance(value['tags_all'], list):
            raise serializers.ValidationError("tags_all deve ser uma lista de IDs.")

        return value

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        segment = super().create(validated_data)
        # Update cached count
        segment.update_cached_count()
        return segment

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        # Update cached count if filters changed
        if 'filters' in validated_data:
            instance.update_cached_count()
        return instance


class SegmentPreviewSerializer(serializers.Serializer):
    """Response serializer for segment preview."""
    count = serializers.IntegerField()
    sample = SupporterListSerializer(many=True)
