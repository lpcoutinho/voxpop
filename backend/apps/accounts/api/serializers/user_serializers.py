from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from apps.accounts.models import User
from apps.tenants.models import TenantMembership


class UserSerializer(serializers.ModelSerializer):
    """Serializer para o usuário autenticado."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'phone',
            'avatar',
            'is_verified',
            'is_superuser',
            'is_staff',
            'force_password_change',
            'date_joined',
        ]
        read_only_fields = ['id', 'email', 'is_verified', 'is_superuser', 'is_staff', 'force_password_change', 'date_joined']


class UserTenantSerializer(serializers.ModelSerializer):
    """Serializer para listar tenants do usuário com sua role."""
    tenant_id = serializers.IntegerField(source='tenant.id')
    tenant_name = serializers.CharField(source='tenant.name')
    tenant_slug = serializers.CharField(source='tenant.slug')
    plan_name = serializers.CharField(source='tenant.plan.name')
    role_display = serializers.CharField(source='get_role_display')

    class Meta:
        model = TenantMembership
        fields = [
            'tenant_id',
            'tenant_name',
            'tenant_slug',
            'plan_name',
            'role',
            'role_display',
            'is_active',
            'created_at',
        ]

class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para troca de senha."""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "As senhas não conferem."})
        return attrs