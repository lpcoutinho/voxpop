"""
Campaign models for VoxPop.
"""
from django.db import models
from django.conf import settings
from django_tenants.models import TenantMixin
from core.models import SoftDeleteModel

class Campaign(SoftDeleteModel):
    """
    Campanha de disparo de mensagens em massa.
    """
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Rascunho'
        SCHEDULED = 'scheduled', 'Agendada'
        RUNNING = 'running', 'Em Andamento'
        PAUSED = 'paused', 'Pausada'
        COMPLETED = 'completed', 'Concluída'
        CANCELLED = 'cancelled', 'Cancelada'
        FAILED = 'failed', 'Falhou'

    name = models.CharField(
        max_length=255,
        verbose_name='Nome da Campanha'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )
    
    # Conteúdo
    message = models.TextField(
        verbose_name='Mensagem'
    )
    media_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='URL da Mídia'
    )
    media_type = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Tipo de Mídia'
    )

    # Configuração de Disparo
    whatsapp_session = models.ForeignKey(
        'whatsapp.WhatsAppSession',
        on_delete=models.PROTECT,
        related_name='campaigns',
        verbose_name='Sessão do WhatsApp'
    )
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Agendada para'
    )
    
    # Segmentação (Filtros salvos)
    target_segment = models.ForeignKey(
        'supporters.Segment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campaigns',
        verbose_name='Segmento Alvo'
    )
    target_tags = models.ManyToManyField(
        'supporters.Tag',
        blank=True,
        verbose_name='Tags Alvo'
    )
    target_groups = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Grupos Alvo',
        help_text='Lista de grupos fixos: leads, supporters, team'
    )
    
    # Status e Controle
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name='Status'
    )
    
    # Métricas (Denormalizadas para performance)
    total_recipients = models.IntegerField(default=0, verbose_name='Total de Destinatários')
    messages_sent = models.IntegerField(default=0, verbose_name='Enviadas')
    messages_delivered = models.IntegerField(default=0, verbose_name='Entregues')
    messages_read = models.IntegerField(default=0, verbose_name='Lidas')
    messages_failed = models.IntegerField(default=0, verbose_name='Falhas')
    
    # Timestamps de Execução
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_campaigns'
    )

    class Meta:
        verbose_name = 'Campanha'
        verbose_name_plural = 'Campanhas'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class CampaignItem(models.Model):
    """
    Item individual da campanha (uma mensagem para um destinatário).
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendente'
        QUEUED = 'queued', 'Na Fila'
        SENT = 'sent', 'Enviada'
        DELIVERED = 'delivered', 'Entregue'
        READ = 'read', 'Lida'
        FAILED = 'failed', 'Falha'

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='items'
    )
    supporter = models.ForeignKey(
        'supporters.Supporter',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campaign_messages'
    )
    
    # Dados históricos (caso o supporter seja deletado)
    recipient_name = models.CharField(max_length=255)
    recipient_phone = models.CharField(max_length=20)
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Integração
    message_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='ID da Mensagem (API)'
    )
    error_message = models.TextField(blank=True)
    
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Item da Campanha'
        verbose_name_plural = 'Itens da Campanha'
        indexes = [
            models.Index(fields=['campaign', 'status']),
            models.Index(fields=['message_id']),
        ]
