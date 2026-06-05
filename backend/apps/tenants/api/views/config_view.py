from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsTenantMember
from ..serializers.config_serializer import TenantConfigSerializer


class TenantConfigView(APIView):
    """
    GET /api/v1/tenants/config/ - Retorna configurações do tenant
    PUT /api/v1/tenants/config/ - Atualiza configurações do tenant
    """
    permission_classes = [IsAuthenticated, IsTenantMember]

    def get(self, request):
        settings = request.tenant.settings or {}
        data = {
            'signature': settings.get('signature', ''),
            'signature_enabled': settings.get('signature_enabled', False),
        }
        serializer = TenantConfigSerializer(data)
        return Response(serializer.data)

    def put(self, request):
        serializer = TenantConfigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        settings = request.tenant.settings or {}
        settings['signature'] = serializer.validated_data.get('signature', '')
        settings['signature_enabled'] = serializer.validated_data.get('signature_enabled', False)
        request.tenant.settings = settings
        request.tenant.save(update_fields=['settings'])

        return Response(serializer.data, status=status.HTTP_200_OK)
