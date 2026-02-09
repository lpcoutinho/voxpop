from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tenants.models import TenantMembership
from ..serializers import UserSerializer, UserTenantSerializer, ChangePasswordSerializer


class MeView(generics.RetrieveUpdateAPIView):
    """
    GET: Retorna os dados do usuário autenticado.
    PATCH/PUT: Atualiza os dados do usuário autenticado.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserTenantsView(APIView):
    """Retorna todos os tenants que o usuário tem acesso."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        memberships = TenantMembership.objects.filter(
            user=request.user,
            is_active=True,
        ).select_related('tenant', 'tenant__plan')

        serializer = UserTenantSerializer(memberships, many=True)
        return Response(serializer.data)

class ChangePasswordView(generics.GenericAPIView):
    """Troca de senha do usuário autenticado."""
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        # Só verificar senha atual se foi fornecida
        old_password = serializer.data.get('old_password')
        if old_password:
            if not user.check_password(old_password):
                return Response({"old_password": ["Senha atual incorreta."]}, status=status.HTTP_400_BAD_REQUEST)
        elif not user.force_password_change:
            # Se não está forçado a trocar senha, exige senha atual
            return Response({"old_password": ["Senha atual é obrigatória."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.data['new_password'])
        user.force_password_change = False  # Reset flag
        user.save()

        return Response({"detail": "Senha alterada com sucesso."}, status=status.HTTP_200_OK)