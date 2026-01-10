"""
Admin views for managing tenants, plans, and users.
Requires superuser permission.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.utils.text import slugify
from django.db import transaction
from django.db.models import Count
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_tenants.utils import schema_context

from apps.tenants.models import Client, Plan, Domain, TenantMembership
from apps.accounts.models import User
from apps.tenants.api.serializers import (
    AdminPlanSerializer,
    AdminPlanCreateSerializer,
    AdminOrganizationSerializer,
    AdminCreateOrganizationSerializer,
    AdminUpdateOrganizationSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
    AdminStatsSerializer,
)
from core.permissions import IsSuperAdmin
from core.pagination import StandardPagination

logger = logging.getLogger(__name__)


# =============================================================================
# Plan Admin ViewSet
# =============================================================================

class AdminPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Plans (superuser only).
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    queryset = Plan.objects.all().order_by('name')
    pagination_class = None  # Plans are few, no need for pagination

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AdminPlanCreateSerializer
        return AdminPlanSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check if any tenants are using this plan
        if instance.clients.exists():
            return Response(
                {'detail': 'Não é possível excluir um plano com organizações vinculadas.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)


# =============================================================================
# Organization Admin ViewSet
# =============================================================================

class AdminOrganizationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Organizations/Clients (superuser only).
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'slug', 'email', 'document']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']
    filterset_fields = ['is_active', 'plan']

    def get_queryset(self):
        # Exclude public schema from organization list
        return Client.objects.select_related('plan').exclude(schema_name='public')

    def get_serializer_class(self):
        if self.action == 'create':
            return AdminCreateOrganizationSerializer
        if self.action in ['update', 'partial_update']:
            return AdminUpdateOrganizationSerializer
        return AdminOrganizationSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create organization with admin owner."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        org_data = serializer.validated_data['organization']
        admin_data = serializer.validated_data['admin']

        # Generate slug
        slug = org_data.get('slug') or slugify(org_data['name'])

        # Get or use default plan
        plan_id = org_data.get('plan_id')
        if plan_id:
            plan = Plan.objects.get(id=plan_id)
        else:
            plan = Plan.objects.filter(is_active=True, is_public=True).first()
            if not plan:
                return Response(
                    {'detail': 'Nenhum plano disponível. Crie um plano primeiro.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Create tenant (Client)
        # Convert empty strings to None for nullable unique fields
        document = org_data.get('document', '').strip() or None
        tenant = Client.objects.create(
            name=org_data['name'],
            slug=slug,
            schema_name=slug.replace('-', '_'),
            document=document,
            email=org_data.get('email', ''),
            phone=org_data.get('phone', ''),
            plan=plan,
            is_active=True,
        )

        # Create domain
        Domain.objects.create(
            domain=f"{slug}.localhost",
            tenant=tenant,
            is_primary=True,
        )

        # Create admin user in tenant schema
        with schema_context(tenant.schema_name):
            user = User.objects.create_user(
                email=admin_data['email'],
                password=admin_data['password'],
                first_name=admin_data['first_name'],
                last_name=admin_data.get('last_name', ''),
                is_verified=True,
            )

        # Create membership as owner (in public schema)
        TenantMembership.objects.create(
            user=user,
            tenant=tenant,
            role='owner',
            is_active=True,
        )

        # Initialize default tenant data (tags, segments, templates)
        from apps.tenants.services.initialization import initialize_tenant_data
        initialize_tenant_data(tenant, admin_user=user)

        logger.info(f"Organization '{tenant.name}' created by superuser {request.user.email}")

        return Response(
            AdminOrganizationSerializer(tenant).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        """Toggle organization active status."""
        organization = self.get_object()
        organization.is_active = not organization.is_active
        organization.save(update_fields=['is_active'])

        logger.info(
            f"Organization '{organization.name}' {'activated' if organization.is_active else 'deactivated'} "
            f"by superuser {request.user.email}"
        )

        return Response(AdminOrganizationSerializer(organization).data)


# =============================================================================
# User Admin ViewSet
# =============================================================================

class AdminUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Users (superuser only).
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['email', 'date_joined', 'last_login']
    ordering = ['-date_joined']
    filterset_fields = ['is_active', 'is_superuser', 'is_verified']
    http_method_names = ['get', 'patch', 'post']  # No delete, no create via this endpoint

    def get_queryset(self):
        return User.objects.all()

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return AdminUserUpdateSerializer
        return AdminUserSerializer

    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        """Reset user password and return temporary password."""
        user = self.get_object()

        # Generate temporary password
        import secrets
        temp_password = secrets.token_urlsafe(12)
        user.set_password(temp_password)
        user.save(update_fields=['password'])

        logger.info(f"Password reset for user {user.email} by superuser {request.user.email}")

        return Response({
            'message': 'Senha resetada com sucesso.',
            'temporary_password': temp_password
        })


# =============================================================================
# Stats View
# =============================================================================

class AdminStatsView(generics.RetrieveAPIView):
    """
    View for admin dashboard statistics.
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = AdminStatsSerializer

    def get_object(self):
        # Count organizations (exclude public schema)
        total_orgs = Client.objects.exclude(schema_name='public').count()
        active_orgs = Client.objects.filter(is_active=True).exclude(schema_name='public').count()

        # Count users
        total_users = User.objects.count()

        # Count supporters and campaigns across all tenants (exclude public schema)
        total_supporters = 0
        total_campaigns = 0
        total_messages = 0
        messages_this_month = 0

        for tenant in Client.objects.filter(is_active=True).exclude(schema_name='public'):
            try:
                with schema_context(tenant.schema_name):
                    from apps.supporters.models import Supporter
                    from apps.campaigns.models import Campaign

                    total_supporters += Supporter.objects.count()
                    total_campaigns += Campaign.objects.count()
            except Exception as e:
                logger.warning(f"Error getting stats for tenant {tenant.slug}: {e}")

        # Recent organizations (exclude public schema)
        recent_orgs = Client.objects.select_related('plan').exclude(schema_name='public').order_by('-created_at')[:5]

        return {
            'total_organizations': total_orgs,
            'active_organizations': active_orgs,
            'total_users': total_users,
            'total_supporters': total_supporters,
            'total_campaigns': total_campaigns,
            'total_messages': total_messages,
            'messages_this_month': messages_this_month,
            'recent_organizations': recent_orgs,
        }
