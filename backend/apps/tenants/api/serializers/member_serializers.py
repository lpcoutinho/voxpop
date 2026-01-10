from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.tenants.models import TenantMembership

User = get_user_model()

class MemberSerializer(serializers.ModelSerializer):
    """Serializer para listar membros."""
    id = serializers.IntegerField(source='user.id', read_only=True)
    name = serializers.CharField(source='user.get_full_name', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    whatsapp = serializers.CharField(source='user.phone', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = TenantMembership
        fields = [
            'id', 'name', 'first_name', 'last_name', 'email', 
            'whatsapp', 'role', 'role_display', 'is_active', 'created_at'
        ]


class AddMemberSerializer(serializers.Serializer):
    """Serializer para adicionar novo membro."""
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    whatsapp = serializers.CharField(max_length=20, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=TenantMembership.Role.choices, default=TenantMembership.Role.VIEWER)

    def validate_email(self, value):
        request = self.context.get('request')
        if request and request.tenant:
            user = User.objects.filter(email=value).first()
            if user:
                if TenantMembership.objects.filter(user=user, tenant=request.tenant).exists():
                    raise serializers.ValidationError("Este usuário já é membro desta organização.")
        return value

class UpdateMemberSerializer(serializers.ModelSerializer):
    """Serializer para atualizar membro e dados do usuário."""
    first_name = serializers.CharField(source='user.first_name', required=False, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', required=False, allow_blank=True)
    email = serializers.EmailField(source='user.email', required=False)
    whatsapp = serializers.CharField(source='user.phone', required=False, allow_blank=True)

    class Meta:
        model = TenantMembership
        fields = ['role', 'is_active', 'first_name', 'last_name', 'email', 'whatsapp']

    def update(self, instance, validated_data):
        # DRF will put nested sources into a dict named after the first part of the source
        user_data = validated_data.pop('user', {})
        
        # Update TenantMembership fields (role, is_active)
        instance = super().update(instance, validated_data)

        # Update User fields
        user = instance.user
        has_changes = False
        
        if 'first_name' in user_data:
            user.first_name = user_data['first_name']
            has_changes = True
        if 'last_name' in user_data:
            user.last_name = user_data['last_name']
            has_changes = True
        if 'email' in user_data:
            user.email = user_data['email']
            has_changes = True
        if 'phone' in user_data:
            user.phone = user_data['phone']
            has_changes = True
            
        if has_changes:
            user.save()
            
        return instance

class EmptySerializer(serializers.Serializer):
    """Serializer vazio para ações que não requerem dados."""
    pass