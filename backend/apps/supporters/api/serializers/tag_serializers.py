"""
Serializers for Tag model.
"""
from rest_framework import serializers

from apps.supporters.models import Tag


class TagSerializer(serializers.ModelSerializer):
    """Full tag serializer for detail view."""
    # Use annotated field from queryset (_supporters_count) or fallback to property
    supporters_count = serializers.SerializerMethodField()
    leads_count = serializers.SerializerMethodField()
    apoiadores_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = [
            'id', 'name', 'slug', 'color', 'description',
            'supporters_count', 'leads_count', 'apoiadores_count',
            'is_active', 'is_system',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'supporters_count', 'is_system']

    def get_supporters_count(self, obj):
        """Get supporters count from annotation or property."""
        # Try annotation first (more efficient), fallback to property
        if hasattr(obj, '_supporters_count'):
            return obj._supporters_count
        return obj.supporters_count

    def get_leads_count(self, obj):
        """Count how many supporters with this tag are leads."""
        try:
            lead_tag = Tag.objects.get(name='Lead', is_system=True)
            return obj.supporters.filter(tags=lead_tag).count()
        except Tag.DoesNotExist:
            return 0

    def get_apoiadores_count(self, obj):
        """Count how many supporters with this tag are apoiadores."""
        try:
            apoiador_tag = Tag.objects.get(name='Apoiador', is_system=True)
            return obj.supporters.filter(tags=apoiador_tag).count()
        except Tag.DoesNotExist:
            return 0


class TagListSerializer(serializers.ModelSerializer):
    """Simplified tag serializer for list view."""
    supporters_count = serializers.SerializerMethodField()
    leads_count = serializers.SerializerMethodField()
    apoiadores_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'color', 'supporters_count', 'leads_count', 'apoiadores_count', 'is_active', 'is_system']

    def get_supporters_count(self, obj):
        """Get supporters count from annotation or property."""
        if hasattr(obj, '_supporters_count'):
            return obj._supporters_count
        return obj.supporters_count

    def get_leads_count(self, obj):
        """Count how many supporters with this tag are leads."""
        try:
            lead_tag = Tag.objects.get(name='Lead', is_system=True)
            return obj.supporters.filter(tags=lead_tag).count()
        except Tag.DoesNotExist:
            return 0

    def get_apoiadores_count(self, obj):
        """Count how many supporters with this tag are apoiadores."""
        try:
            apoiador_tag = Tag.objects.get(name='Apoiador', is_system=True)
            return obj.supporters.filter(tags=apoiador_tag).count()
        except Tag.DoesNotExist:
            return 0


class TagCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating tags."""

    class Meta:
        model = Tag
        fields = ['name', 'color', 'description', 'is_active']

    def validate_name(self, value):
        """Validate tag name is unique (case-insensitive)."""
        qs = Tag.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Tag com este nome já existe.")
        return value

    def validate_color(self, value):
        """Validate color is a valid hex color."""
        if value and not value.startswith('#'):
            value = f'#{value}'
        if len(value) != 7:
            raise serializers.ValidationError("Cor deve ser um código hex válido (ex: #6366f1)")
        return value

    def validate(self, attrs):
        """Prevent modification of system tags."""
        if self.instance and self.instance.is_system:
            # Allow only color and description changes for system tags
            allowed_fields = {'color', 'description'}
            changed_fields = set(attrs.keys()) - allowed_fields
            if changed_fields:
                raise serializers.ValidationError(
                    f"Tags de sistema só podem ter cor e descrição alteradas. "
                    f"Campos não permitidos: {changed_fields}"
                )
        return attrs
