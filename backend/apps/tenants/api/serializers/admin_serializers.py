"""
Admin serializers for managing tenants, plans, and users.
Requires superuser permission.
"""
from django.utils.text import slugify
from django.db import models
from rest_framework import serializers

from apps.tenants.models import Client, Plan, Domain, TenantMembership
from apps.accounts.models import User


# =============================================================================
# Plan Admin Serializers
# =============================================================================

class AdminPlanSerializer(serializers.ModelSerializer):
    """Full plan serializer for admin."""
    tenants_count = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'slug', 'description',
            'max_supporters', 'max_messages_month',
            'max_campaigns', 'max_whatsapp_sessions',
            'price', 'is_active', 'is_public',
            'tenants_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'tenants_count', 'created_at', 'updated_at']

    def get_tenants_count(self, obj):
        return obj.clients.filter(is_active=True).count()


class AdminPlanCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating plans."""

    class Meta:
        model = Plan
        fields = [
            'name', 'description',
            'max_supporters', 'max_messages_month',
            'max_campaigns', 'max_whatsapp_sessions',
            'price', 'is_active', 'is_public'
        ]

    def create(self, validated_data):
        validated_data['slug'] = slugify(validated_data['name'])
        return super().create(validated_data)


# =============================================================================
# Organization (Client) Admin Serializers
# =============================================================================

class OwnerSerializer(serializers.Serializer):
    """Nested serializer for owner info."""
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.get_full_name() or obj.email


class AdminOrganizationSerializer(serializers.ModelSerializer):
    """Full organization serializer for admin list/detail."""
    plan = AdminPlanSerializer(read_only=True)
    owner = serializers.SerializerMethodField()
    supporters_count = serializers.SerializerMethodField()
    campaigns_count = serializers.SerializerMethodField()
    messages_sent = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            'id', 'name', 'slug', 'schema_name',
            'document', 'email', 'phone',
            'plan', 'is_active', 'settings',
            'owner', 'supporters_count', 'campaigns_count', 'messages_sent',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'schema_name', 'created_at', 'updated_at']

    def get_owner(self, obj):
        membership = TenantMembership.objects.filter(
            tenant=obj, role='owner', is_active=True
        ).select_related('user').first()
        if membership:
            return OwnerSerializer(membership.user).data
        return None

    def get_supporters_count(self, obj):
        try:
            stats = obj.get_usage_stats()
            return stats.get('supporters_count', 0)
        except Exception:
            return 0

    def get_campaigns_count(self, obj):
        try:
            stats = obj.get_usage_stats()
            return stats.get('campaigns_count', 0)
        except Exception:
            return 0

    def get_messages_sent(self, obj):
        # This could be expensive, so return 0 for list view
        return 0


class AdminCreateOwnerSerializer(serializers.Serializer):
    """Serializer for owner data when creating organization."""
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Este email já está cadastrado.')
        return value.lower()


class AdminCreateOrganizationSerializer(serializers.Serializer):
    """Serializer for creating organization with admin owner."""
    organization = serializers.DictField(child=serializers.CharField())
    admin = AdminCreateOwnerSerializer()

    def validate_organization(self, value):
        name = value.get('name')
        if not name:
            raise serializers.ValidationError({'name': 'Nome é obrigatório.'})

        # Validate slug uniqueness
        slug = value.get('slug') or slugify(name)
        if Client.objects.filter(slug=slug).exists():
            raise serializers.ValidationError({'slug': 'Já existe uma organização com este slug.'})

        # Validate plan if provided
        plan_id = value.get('plan_id')
        if plan_id:
            if not Plan.objects.filter(id=plan_id, is_active=True).exists():
                raise serializers.ValidationError({'plan_id': 'Plano inválido ou inativo.'})

        return value


class AdminUpdateOrganizationSerializer(serializers.ModelSerializer):
    """Serializer for updating organization."""
    plan_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Client
        fields = ['name', 'document', 'email', 'phone', 'plan_id', 'is_active']

    def validate_plan_id(self, value):
        if value and not Plan.objects.filter(id=value).exists():
            raise serializers.ValidationError('Plano não encontrado.')
        return value

    def update(self, instance, validated_data):
        plan_id = validated_data.pop('plan_id', None)
        if plan_id:
            instance.plan_id = plan_id
        return super().update(instance, validated_data)


# =============================================================================
# User Admin Serializers
# =============================================================================

class UserOrganizationSerializer(serializers.Serializer):
    """Nested serializer for user's organizations."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    role = serializers.CharField()


class AdminUserSerializer(serializers.ModelSerializer):
    """Full user serializer for admin."""
    name = serializers.SerializerMethodField()
    organizations = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'first_name', 'last_name',
            'is_active', 'is_verified', 'is_superuser', 'is_staff',
            'organizations', 'last_login', 'date_joined'
        ]
        read_only_fields = ['id', 'email', 'is_superuser', 'last_login', 'date_joined']

    def get_name(self, obj):
        return obj.get_full_name() or obj.email

    def get_organizations(self, obj):
        memberships = TenantMembership.objects.filter(
            user=obj, is_active=True
        ).select_related('tenant')

        return [
            {
                'id': m.tenant.id,
                'name': m.tenant.name,
                'role': m.role
            }
            for m in memberships
        ]


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'is_active', 'is_verified']


# =============================================================================
# Stats Serializer
# =============================================================================

class AdminStatsSerializer(serializers.Serializer):
    """Serializer for admin dashboard stats."""
    total_organizations = serializers.IntegerField()
    active_organizations = serializers.IntegerField()
    total_users = serializers.IntegerField()
    total_supporters = serializers.IntegerField()
    total_campaigns = serializers.IntegerField()
    total_messages = serializers.IntegerField()
    messages_this_month = serializers.IntegerField()
    recent_organizations = AdminOrganizationSerializer(many=True)
