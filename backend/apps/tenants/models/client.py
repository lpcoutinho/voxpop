"""
Tenant model for VoxPop multi-tenancy.
Each political campaign/organization is a Client with its own PostgreSQL schema.
"""
from django.db import models
from django_tenants.models import TenantMixin


class Client(TenantMixin):
    """
    Tenant principal - cada organização política é um Client.
    Herda schema_name de TenantMixin (cria schema PostgreSQL separado).
    """
    name = models.CharField(
        max_length=255,
        verbose_name='Nome da Organização'
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='Slug'
    )
    document = models.CharField(
        max_length=18,
        unique=True,
        blank=True,
        null=True,
        verbose_name='CNPJ',
        help_text='CNPJ da organização (formato: XX.XXX.XXX/XXXX-XX)'
    )
    plan = models.ForeignKey(
        'Plan',
        on_delete=models.PROTECT,
        related_name='clients',
        verbose_name='Plano'
    )

    # Configurações do tenant
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )
    settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Configurações',
        help_text='Configurações personalizadas do tenant em JSON'
    )

    # Contato
    email = models.EmailField(
        verbose_name='E-mail',
        blank=True
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Telefone'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    # django-tenants: auto-criar schema e auto-dropar
    auto_create_schema = True
    auto_drop_schema = True

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_usage_stats(self) -> dict:
        """Retorna estatísticas de uso do tenant."""
        # Schema público não tem tabelas de tenant
        if self.schema_name == 'public':
            return {
                'supporters_count': 0,
                'campaigns_count': 0,
                'active_sessions': 0,
            }

        # Import local para evitar circular import
        from django_tenants.utils import schema_context

        try:
            with schema_context(self.schema_name):
                from apps.supporters.models import Supporter
                from apps.campaigns.models import Campaign
                from apps.whatsapp.models import WhatsAppSession

                return {
                    'supporters_count': Supporter.objects.count(),
                    'campaigns_count': Campaign.objects.count(),
                    'active_sessions': WhatsAppSession.objects.filter(
                        status='connected'
                    ).count(),
                }
        except Exception:
            return {
                'supporters_count': 0,
                'campaigns_count': 0,
                'active_sessions': 0,
            }
