from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.tenants.models import Plan
from ..serializers import PlanSerializer


class PlanListView(generics.ListAPIView):
    """Lista os planos públicos disponíveis."""
    queryset = Plan.objects.filter(is_active=True, is_public=True)
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]
    pagination_class = None
