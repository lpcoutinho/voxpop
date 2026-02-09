from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.teams.models import TeamMember


User = get_user_model()


class TeamMemberListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem"""
    display_name = serializers.CharField(read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    department_display = serializers.CharField(source='get_department_display', read_only=True)
    pending = serializers.BooleanField(read_only=True)

    class Meta:
        model = TeamMember
        fields = [
            'id', 'display_name', 'user_email', 'role', 'role_display',
            'department', 'department_display', 'is_active', 'pending', 'created_at'
        ]


class TeamMemberDetailSerializer(serializers.ModelSerializer):
    """Serializer completo com detalhes do usuário"""
    user_details = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    department_display = serializers.CharField(source='get_department_display', read_only=True)
    is_admin_role = serializers.BooleanField(read_only=True)
    can_manage_campaigns = serializers.BooleanField(read_only=True)
    can_view_data = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = TeamMember
        fields = [
            'id', 'user', 'user_details', 'role', 'role_display',
            'department', 'department_display', 'is_active', 'notes',
            'is_admin_role', 'can_manage_campaigns', 'can_view_data',
            'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def get_user_details(self, obj):
        """Retorna detalhes do usuário associado"""
        user = obj.user
        return {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'avatar': user.avatar.url if user.avatar else None,
            'is_verified': user.is_verified
        }


class TeamMemberCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de novo membro"""
    email = serializers.EmailField(write_only=True, required=True)
    first_name = serializers.CharField(write_only=True, required=True)
    last_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    send_whatsapp_credentials = serializers.BooleanField(
        write_only=True, 
        default=True,
        help_text="Enviar credenciais de acesso por WhatsApp"
    )
    
    class Meta:
        model = TeamMember
        fields = [
            'email', 'first_name', 'last_name', 'phone', 'role', 
            'department', 'notes', 'send_whatsapp_credentials', 'is_active'
        ]
    
    def validate_email(self, value):
        """Valida se email já existe no tenant"""
        if User.objects.filter(email=value).exists():
            # Se usuário já existe, verificar se já é membro da equipe
            if TeamMember.objects.filter(user__email=value).exists():
                raise serializers.ValidationError(
                    'Este usuário já é membro da equipe.'
                )
        return value
    
    def create(self, validated_data):
        """Cria usuário e membro da equipe"""
        # Extrair dados do usuário
        user_data = {
            'email': validated_data.pop('email'),
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name', ''),
            'phone': validated_data.pop('phone', ''),
        }
        send_whatsapp = validated_data.pop('send_whatsapp_credentials', True)
        
        # Criar ou obter usuário
        user, created = User.objects.get_or_create(
            email=user_data['email'],
            defaults=user_data
        )
        
        # Se usuário novo, criar senha temporária
        if created:
            temp_password = User.objects.make_random_password(length=8)
            user.set_password(temp_password)
            user.save()
        else:
            temp_password = None
        
        # Criar TeamMember
        team_member = TeamMember.objects.create(
            user=user,
            created_by=self.context['request'].user,
            **validated_data
        )
        
        # Enviar credenciais por WhatsApp se solicitado
        if send_whatsapp and user.phone:
            from .services import TeamMemberService
            service = TeamMemberService()
            service.send_credentials_via_whatsapp(
                user=user,
                temp_password=temp_password,
                role=team_member.role
            )
        
        return team_member


class TeamMemberUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualização de membro"""
    role = serializers.ChoiceField(choices=TeamMember.ROLE_CHOICES)
    
    class Meta:
        model = TeamMember
        fields = [
            'role', 'department', 'is_active', 'notes'
        ]
    
    def update(self, instance, validated_data):
        """Atualiza membro com log de alterações"""
        # Log de mudanças se role for alterado
        if 'role' in validated_data and validated_data['role'] != instance.role:
            # Adicionar observação sobre mudança de role
            notes_change = f"Role alterado de {instance.get_role_display()} para {TeamMember.ROLE_CHOICES[validated_data['role']][1]}"
            if instance.notes:
                validated_data['notes'] = f"{instance.notes}\n\n{notes_change}"
            else:
                validated_data['notes'] = notes_change
        
        return super().update(instance, validated_data)