import logging
import secrets
import string

from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404

from apps.tenants.models import TenantMembership
from apps.tenants.api.serializers.member_serializers import (
    MemberSerializer, 
    AddMemberSerializer, 
    UpdateMemberSerializer,
    EmptySerializer
)
from apps.whatsapp.models import WhatsAppSession
from apps.whatsapp.services.whatsapp_service import whatsapp_service

logger = logging.getLogger(__name__)
User = get_user_model()

class MemberViewSet(viewsets.ModelViewSet):
    """
    Gerencia membros do tenant atual.
    """
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete'] 

    def get_queryset(self):
        # Retorna apenas memberships do tenant atual
        if not hasattr(self.request, 'tenant'):
            return TenantMembership.objects.none()
        return TenantMembership.objects.filter(tenant=self.request.tenant).select_related('user')

    def get_serializer_class(self):
        if self.action == 'create':
            return AddMemberSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateMemberSerializer
        elif self.action == 'reset_password':
            return EmptySerializer
        return MemberSerializer

    def get_object(self):
        queryset = self.get_queryset()
        user_id = self.kwargs.get('pk')
        obj = get_object_or_404(queryset, user__id=user_id)
        self.check_object_permissions(self.request, obj)
        return obj

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        tenant = request.tenant
        email = data['email']
        whatsapp_number = data.get('whatsapp')

        try:
            with transaction.atomic():
                # 1. Obter ou Criar Usuário
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'first_name': data['first_name'],
                        'last_name': data['last_name'],
                        'is_verified': True,
                        'phone': whatsapp_number or ''
                    }
                )

                # Se o usuário já existia mas não tinha telefone, atualiza
                if not created and whatsapp_number and not user.phone:
                    user.phone = whatsapp_number
                    user.save()

                password = None
                if created:
                    # Gerar senha aleatória (simples, max 8 caracteres)
                    password = self._generate_simple_password()
                    user.set_password(password)
                    user.force_password_change = True
                    user.save()

                # 2. Criar Membership
                membership = TenantMembership.objects.create(
                    user=user,
                    tenant=tenant,
                    role=data['role']
                )

                # 3. Enviar WhatsApp (se houver número e senha gerada ou apenas notificação)
                if whatsapp_number:
                    self._send_welcome_whatsapp(tenant, user, whatsapp_number, password, created)

                # Serializar resposta
                response_serializer = MemberSerializer(membership)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Erro ao adicionar membro: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Erro ao processar solicitação."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_destroy(self, instance):
        # Remove apenas a associação com o tenant
        instance.delete()

    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        """Reseta a senha do usuário e envia via WhatsApp cadastrado."""
        membership = self.get_object()
        user = membership.user
        tenant = request.tenant
        
        whatsapp_number = user.phone

        if not whatsapp_number:
            return Response(
                {"detail": "Usuário não possui número de WhatsApp cadastrado."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 1. Gerar nova senha
            new_password = self._generate_simple_password()
            user.set_password(new_password)
            user.force_password_change = True
            user.save()

            # 2. Enviar via WhatsApp
            session = WhatsAppSession.objects.filter(status='connected', is_active=True).first()
            if not session:
                return Response(
                    {"detail": f"Senha resetada para '{new_password}', mas não foi possível enviar WhatsApp (nenhuma sessão ativa)."},
                    status=status.HTTP_200_OK
                )

            message = (
                f"Olá {user.first_name}!\n\n"
                f"Sua senha de acesso ao *{tenant.name}* foi redefinida.\n\n"
                f"🔑 Nova Senha: {new_password}\n\n"
                f"Acesse em: http://{tenant.domains.first().domain}:5173"
            )

            whatsapp_service.send_text_sync(
                instance_name=session.instance_name,
                phone=whatsapp_number,
                text=message,
                api_key=session.access_token
            )

            return Response({"detail": "Senha resetada e enviada com sucesso."}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Erro ao resetar senha: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Erro ao resetar senha."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _generate_simple_password(self):
        chars = string.ascii_letters + string.digits + "._@"
        return ''.join(secrets.choice(chars) for _ in range(8))

    def _send_welcome_whatsapp(self, tenant, user, phone, password, is_new_user):
        """Tenta enviar mensagem via WhatsApp do tenant."""
        try:
            session = WhatsAppSession.objects.filter(status='connected', is_active=True).first()
            if not session:
                logger.warning(f"Nenhuma sessão WhatsApp ativa para enviar convite no tenant {tenant.name}")
                return

            if is_new_user and password:
                message = (
                    f"Olá {user.first_name}!\n\n"
                    f"Você foi adicionado à equipe *{tenant.name}* no VoxPop.\n\n"
                    f"Suas credenciais de acesso:\n"
                    f"📧 Email: {user.email}\n"
                    f"🔑 Senha: {password}\n\n"
                    f"Acesse em: http://{tenant.domains.first().domain}:5173"
                )
            else:
                message = (
                    f"Olá {user.first_name}!\n\n"
                    f"Você foi adicionado à equipe *{tenant.name}* no VoxPop.\n\n"
                    f"Acesse com seu email e senha existentes em:\n"
                    f"http://{tenant.domains.first().domain}:5173"
                )

            whatsapp_service.send_text_sync(
                instance_name=session.instance_name,
                phone=phone,
                text=message,
                api_key=session.access_token
            )

        except Exception as e:
            logger.error(f"Falha ao enviar WhatsApp de boas-vindas: {str(e)}")
