"""
Custom tenant middleware to support X-Tenant header.
"""
from django.db import connection
from django.core.exceptions import DisallowedHost
from django_tenants.middleware.main import TenantMainMiddleware
from django_tenants.utils import get_tenant_model, get_tenant_domain_model


class TenantHeaderMiddleware(TenantMainMiddleware):
    """
    Middleware that allows tenant selection via X-Tenant header.
    Falls back to domain-based tenant selection if header is not present.

    This is useful for development where frontend and backend
    are on different origins.
    """

    TENANT_HEADER = 'HTTP_X_TENANT'

    def process_request(self, request):
        """
        Override process_request to check for X-Tenant header first.
        """
        # Check for X-Tenant header (slug-based)
        tenant_slug = request.META.get(self.TENANT_HEADER)
        if tenant_slug:
            TenantModel = get_tenant_model()
            try:
                tenant = TenantModel.objects.get(slug=tenant_slug, is_active=True)
                request.tenant = tenant
                connection.set_tenant(tenant)
                return None
            except TenantModel.DoesNotExist:
                pass  # Fall through to default behavior

        # Fall back to domain-based tenant selection
        return super().process_request(request)
