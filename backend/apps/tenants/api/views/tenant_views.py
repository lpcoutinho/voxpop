from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.tenants.services import TenantService
from ..serializers import TenantCreateSerializer


class TenantCreateView(generics.CreateAPIView):
    """
    Endpoint para registro de novo tenant.
    Cria o tenant, domínio, usuário owner e membership.
    """
    serializer_class = TenantCreateSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = TenantService()
        result = service.create_tenant_with_owner(
            tenant_data=serializer.validated_data['tenant'],
            owner_data=serializer.validated_data['owner'],
            domain=serializer.validated_data['domain'],
        )

        return Response(
            {
                'message': 'Tenant criado com sucesso',
                'tenant': {
                    'id': result['tenant'].id,
                    'name': result['tenant'].name,
                    'schema_name': result['tenant'].schema_name,
                },
                'domain': result['domain'].domain,
                'owner': {
                    'id': result['owner'].id,
                    'email': result['owner'].email,
                },
            },
            status=status.HTTP_201_CREATED
        )
