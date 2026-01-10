"""
Serializers for Supporter model.
"""
from rest_framework import serializers

from apps.supporters.models import Supporter, Tag, SupporterTag
from core.utils import clean_phone_number, validate_cpf, clean_document


class TagNestedSerializer(serializers.ModelSerializer):
    """Simplified tag for nested display in Supporter."""

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'color', 'is_system']


class SupporterListSerializer(serializers.ModelSerializer):
    """Serializer for listing supporters."""
    tags = TagNestedSerializer(many=True, read_only=True)
    is_lead = serializers.BooleanField(read_only=True)
    is_supporter_status = serializers.BooleanField(read_only=True)
    is_blacklisted = serializers.BooleanField(read_only=True)
    contact_status = serializers.CharField(read_only=True)

    class Meta:
        model = Supporter
        fields = [
            'id', 'name', 'phone', 'email', 'city', 'state',
            'tags', 'whatsapp_opt_in', 'created_at',
            'is_lead', 'is_supporter_status', 'is_blacklisted', 'contact_status'
        ]


class SupporterDetailSerializer(serializers.ModelSerializer):
    """Full serializer for supporter detail view."""
    tags = TagNestedSerializer(many=True, read_only=True)
    age = serializers.IntegerField(read_only=True)
    can_receive_messages = serializers.BooleanField(read_only=True)
    is_lead = serializers.BooleanField(read_only=True)
    is_supporter_status = serializers.BooleanField(read_only=True)
    is_blacklisted = serializers.BooleanField(read_only=True)
    contact_status = serializers.CharField(read_only=True)

    class Meta:
        model = Supporter
        fields = [
            'id', 'name', 'phone', 'email', 'cpf',
            'city', 'neighborhood', 'state', 'zip_code',
            'electoral_zone', 'electoral_section',
            'birth_date', 'gender', 'age',
            'whatsapp_opt_in', 'opt_in_date',
            'source', 'extra_data',
            'tags', 'can_receive_messages',
            'is_lead', 'is_supporter_status', 'is_blacklisted', 'contact_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'age', 'can_receive_messages',
            'is_lead', 'is_supporter_status', 'is_blacklisted', 'contact_status'
        ]


class SupporterCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating supporters."""
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        default=list
    )
    initial_status = serializers.ChoiceField(
        choices=['lead', 'apoiador'],
        write_only=True,
        required=False,
        default='lead',
        help_text='Status inicial do contato: lead ou apoiador'
    )

    class Meta:
        model = Supporter
        fields = [
            'name', 'phone', 'email', 'cpf',
            'city', 'neighborhood', 'state', 'zip_code',
            'electoral_zone', 'electoral_section',
            'birth_date', 'gender',
            'whatsapp_opt_in', 'extra_data',
            'tag_ids', 'initial_status'
        ]

    def validate_phone(self, value):
        """Normalize and validate phone number."""
        cleaned = clean_phone_number(value)
        if not cleaned:
            raise serializers.ValidationError("Telefone inválido. Use formato: +5511999999999")

        # Check uniqueness
        qs = Supporter.objects.filter(phone=cleaned)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Já existe um apoiador com este telefone.")

        return cleaned

    def validate_cpf(self, value):
        """Validate and clean CPF."""
        if not value:
            return ''
        cleaned = clean_document(value)
        if cleaned and not validate_cpf(cleaned):
            raise serializers.ValidationError("CPF inválido.")
        return cleaned

    def validate_tag_ids(self, value):
        """Validate tag IDs exist."""
        if value:
            existing_ids = set(Tag.objects.filter(id__in=value, is_active=True).values_list('id', flat=True))
            invalid_ids = set(value) - existing_ids
            if invalid_ids:
                raise serializers.ValidationError(f"Tags não encontradas: {invalid_ids}")
        return value

    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        initial_status = validated_data.pop('initial_status', 'lead')
        validated_data['source'] = 'manual'

        supporter = super().create(validated_data)

        # Add custom tags
        if tag_ids:
            for tag_id in tag_ids:
                SupporterTag.objects.create(supporter=supporter, tag_id=tag_id)

        # Set initial status based on parameter
        if initial_status == 'apoiador':
            supporter.promote_to_supporter()
        else:
            supporter.set_as_lead()

        return supporter


class SupporterUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating supporters."""
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Supporter
        fields = [
            'name', 'phone', 'email', 'cpf',
            'city', 'neighborhood', 'state', 'zip_code',
            'electoral_zone', 'electoral_section',
            'birth_date', 'gender',
            'whatsapp_opt_in', 'extra_data',
            'tag_ids'
        ]

    def validate_phone(self, value):
        """Normalize and validate phone number."""
        cleaned = clean_phone_number(value)
        if not cleaned:
            raise serializers.ValidationError("Telefone inválido.")

        # Check uniqueness excluding current instance
        qs = Supporter.objects.filter(phone=cleaned).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Já existe um apoiador com este telefone.")

        return cleaned

    def validate_cpf(self, value):
        """Validate and clean CPF."""
        if not value:
            return ''
        cleaned = clean_document(value)
        if cleaned and not validate_cpf(cleaned):
            raise serializers.ValidationError("CPF inválido.")
        return cleaned

    def validate_tag_ids(self, value):
        """Validate tag IDs exist and are not system tags."""
        if value is not None:
            # Only validate non-system tags
            existing_ids = set(
                Tag.objects.filter(id__in=value, is_active=True, is_system=False)
                .values_list('id', flat=True)
            )
            invalid_ids = set(value) - existing_ids
            if invalid_ids:
                # Check if any are system tags
                system_tag_ids = set(
                    Tag.objects.filter(id__in=invalid_ids, is_system=True)
                    .values_list('id', flat=True)
                )
                if system_tag_ids:
                    raise serializers.ValidationError(
                        f"Tags de sistema não podem ser atribuídas manualmente: {system_tag_ids}"
                    )
                raise serializers.ValidationError(f"Tags não encontradas: {invalid_ids}")
        return value

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)

        instance = super().update(instance, validated_data)

        # Update tags if provided (only non-system tags)
        if tag_ids is not None:
            # Remove only non-system tags (preserve system tags like Lead, Apoiador, Blacklist)
            SupporterTag.objects.filter(
                supporter=instance,
                tag__is_system=False
            ).delete()
            # Add new non-system tags
            for tag_id in tag_ids:
                # Only add if it's not a system tag
                tag = Tag.objects.filter(id=tag_id, is_system=False).first()
                if tag:
                    SupporterTag.objects.get_or_create(supporter=instance, tag=tag)

        return instance


class SupporterTagsSerializer(serializers.Serializer):
    """Serializer for adding/removing tags from a supporter."""
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )

    def validate_tag_ids(self, value):
        """Validate tag IDs exist."""
        if not value:
            raise serializers.ValidationError("Informe pelo menos uma tag.")
        existing_ids = set(Tag.objects.filter(id__in=value, is_active=True).values_list('id', flat=True))
        invalid_ids = set(value) - existing_ids
        if invalid_ids:
            raise serializers.ValidationError(f"Tags não encontradas: {invalid_ids}")
        return value


class SupporterBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk actions on supporters."""
    supporter_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        min_length=1,
        help_text='Lista de IDs de contatos para a ação'
    )

    def validate_supporter_ids(self, value):
        """Validate supporter IDs exist."""
        existing_ids = set(
            Supporter.objects.filter(id__in=value).values_list('id', flat=True)
        )
        invalid_ids = set(value) - existing_ids
        if invalid_ids:
            raise serializers.ValidationError(f"Contatos não encontrados: {invalid_ids}")
        return value


class SupporterStatusChangeSerializer(serializers.Serializer):
    """Response serializer for status change operations."""
    success = serializers.BooleanField()
    message = serializers.CharField()
    updated_count = serializers.IntegerField()
