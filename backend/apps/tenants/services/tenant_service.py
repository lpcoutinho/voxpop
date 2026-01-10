"""
Service layer for tenant operations.
"""
import logging
from typing import Any

from django.db import transaction
from django.utils.text import slugify

from apps.tenants.models import Client, Domain, Plan, TenantMembership

logger = logging.getLogger(__name__)


class TenantService:
    """Service para operações relacionadas a tenants."""

    @transaction.atomic
    def create_tenant_with_owner(
        self,
        tenant_data: dict[str, Any],
        owner_data: dict[str, Any],
        domain: str,
    ) -> dict:
        """
        Cria um novo tenant com seu owner.

        Args:
            tenant_data: Dados do tenant (name, document, plan_id, etc)
            owner_data: Dados do owner (email, password, first_name, etc)
            domain: Domínio para o tenant

        Returns:
            Dict com tenant, domain e owner criados
        """
        # Import local para evitar circular import
        from apps.accounts.models import User

        # 1. Criar o usuário owner
        user = User.objects.create_user(
            email=owner_data['email'],
            password=owner_data['password'],
            first_name=owner_data['first_name'],
            last_name=owner_data.get('last_name', ''),
            phone=owner_data.get('phone', ''),
        )
        logger.info(f"Usuário criado: {user.email}")

        # 2. Buscar o plano
        plan = Plan.objects.get(id=tenant_data['plan_id'])

        # 3. Criar o tenant
        slug = slugify(tenant_data['name'])
        schema_name = slug.replace('-', '_')

        tenant = Client.objects.create(
            schema_name=schema_name,
            name=tenant_data['name'],
            slug=slug,
            document=tenant_data['document'],
            plan=plan,
            email=tenant_data.get('email', user.email),
            phone=tenant_data.get('phone', ''),
        )
        logger.info(f"Tenant criado: {tenant.name} (schema: {tenant.schema_name})")

        # 4. Criar o domínio
        tenant_domain = Domain.objects.create(
            domain=domain,
            tenant=tenant,
            is_primary=True,
        )
        logger.info(f"Domínio criado: {tenant_domain.domain}")

        # 5. Criar membership como owner
        membership = TenantMembership.objects.create(
            user=user,
            tenant=tenant,
            role=TenantMembership.Role.OWNER,
        )
        logger.info(f"Membership criada: {membership}")

        return {
            'tenant': tenant,
            'domain': tenant_domain,
            'owner': user,
            'membership': membership,
        }

    def get_tenant_stats(self, tenant: Client) -> dict:
        """Retorna estatísticas do tenant."""
        return tenant.get_usage_stats()

    def check_plan_limits(self, tenant: Client) -> dict:
        """Verifica se o tenant está dentro dos limites do plano."""
        stats = self.get_tenant_stats(tenant)
        plan = tenant.plan

        return {
            'supporters': {
                'current': stats['supporters_count'],
                'limit': plan.max_supporters,
                'exceeded': stats['supporters_count'] >= plan.max_supporters,
            },
            'campaigns': {
                'current': stats['campaigns_count'],
                'limit': plan.max_campaigns,
                'exceeded': stats['campaigns_count'] >= plan.max_campaigns,
            },
            'whatsapp_sessions': {
                'current': stats['active_sessions'],
                'limit': plan.max_whatsapp_sessions,
                'exceeded': stats['active_sessions'] >= plan.max_whatsapp_sessions,
            },
        }
