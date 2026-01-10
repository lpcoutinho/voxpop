"""
Plan model for VoxPop subscription tiers.
"""
from django.db import models


class Plan(models.Model):
    """
    Planos de assinatura disponíveis para os tenants.
    """
    name = models.CharField(
        max_length=100,
        verbose_name='Nome do Plano'
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name='Slug'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )

    # Limites
    max_supporters = models.IntegerField(
        verbose_name='Máximo de Apoiadores',
        help_text='Número máximo de apoiadores cadastrados'
    )
    max_messages_month = models.IntegerField(
        verbose_name='Mensagens por Mês',
        help_text='Número máximo de mensagens enviadas por mês'
    )
    max_campaigns = models.IntegerField(
        verbose_name='Máximo de Campanhas',
        help_text='Número máximo de campanhas ativas simultaneamente'
    )
    max_whatsapp_sessions = models.IntegerField(
        verbose_name='Sessões WhatsApp',
        help_text='Número máximo de sessões WhatsApp conectadas'
    )

    # Preço
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Preço Mensal'
    )

    # Features extras em JSON
    features = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Features',
        help_text='Features adicionais do plano em JSON'
    )

    # Controle
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name='Público',
        help_text='Se o plano aparece na página de preços'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'
        ordering = ['price']

    def __str__(self):
        return f"{self.name} - R${self.price}/mês"
