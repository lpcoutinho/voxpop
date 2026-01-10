"""
Metrics models for dashboard analytics.
"""
from django.db import models

from core.models import BaseModel


class DailyMetrics(BaseModel):
    """
    Métricas agregadas por dia.
    Armazena estatísticas diárias para o dashboard.
    """

    date = models.DateField(
        unique=True,
        verbose_name='Data'
    )

    # Apoiadores
    new_supporters = models.PositiveIntegerField(
        default=0,
        verbose_name='Novos Apoiadores'
    )
    total_supporters = models.PositiveIntegerField(
        default=0,
        verbose_name='Total de Apoiadores'
    )

    # Mensagens
    messages_sent = models.PositiveIntegerField(
        default=0,
        verbose_name='Mensagens Enviadas'
    )
    messages_delivered = models.PositiveIntegerField(
        default=0,
        verbose_name='Mensagens Entregues'
    )
    messages_read = models.PositiveIntegerField(
        default=0,
        verbose_name='Mensagens Lidas'
    )
    messages_failed = models.PositiveIntegerField(
        default=0,
        verbose_name='Mensagens com Falha'
    )

    # Campanhas
    campaigns_created = models.PositiveIntegerField(
        default=0,
        verbose_name='Campanhas Criadas'
    )
    campaigns_completed = models.PositiveIntegerField(
        default=0,
        verbose_name='Campanhas Concluídas'
    )

    # Taxas calculadas
    delivery_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='Taxa de Entrega (%)'
    )
    read_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='Taxa de Leitura (%)'
    )

    class Meta:
        verbose_name = 'Métricas Diárias'
        verbose_name_plural = 'Métricas Diárias'
        ordering = ['-date']

    def __str__(self):
        return f"Métricas de {self.date}"

    def calculate_rates(self) -> None:
        """Calcula as taxas de entrega e leitura."""
        if self.messages_sent > 0:
            self.delivery_rate = round(
                (self.messages_delivered / self.messages_sent) * 100, 2
            )
        else:
            self.delivery_rate = 0

        if self.messages_delivered > 0:
            self.read_rate = round(
                (self.messages_read / self.messages_delivered) * 100, 2
            )
        else:
            self.read_rate = 0

    def save(self, *args, **kwargs):
        self.calculate_rates()
        super().save(*args, **kwargs)


class CampaignMetrics(BaseModel):
    """
    Métricas detalhadas por campanha.
    Armazena estatísticas agregadas de uma campanha específica.
    """

    campaign = models.OneToOneField(
        'campaigns.Campaign',
        on_delete=models.CASCADE,
        related_name='metrics',
        verbose_name='Campanha'
    )

    # Contagens
    total_recipients = models.PositiveIntegerField(
        default=0,
        verbose_name='Total de Destinatários'
    )
    sent = models.PositiveIntegerField(
        default=0,
        verbose_name='Enviadas'
    )
    delivered = models.PositiveIntegerField(
        default=0,
        verbose_name='Entregues'
    )
    read = models.PositiveIntegerField(
        default=0,
        verbose_name='Lidas'
    )
    failed = models.PositiveIntegerField(
        default=0,
        verbose_name='Falhas'
    )

    # Taxas
    delivery_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='Taxa de Entrega (%)'
    )
    read_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='Taxa de Leitura (%)'
    )
    failure_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='Taxa de Falha (%)'
    )

    # Tempo médio
    avg_delivery_time_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Tempo Médio de Entrega (s)'
    )

    last_calculated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Atualização'
    )

    class Meta:
        verbose_name = 'Métricas da Campanha'
        verbose_name_plural = 'Métricas das Campanhas'

    def __str__(self):
        return f"Métricas de {self.campaign.name}"

    def sync_from_campaign(self) -> None:
        """Sincroniza métricas a partir da campanha."""
        campaign = self.campaign
        self.total_recipients = campaign.total_recipients
        self.sent = campaign.sent_count
        self.delivered = campaign.delivered_count
        self.read = campaign.read_count
        self.failed = campaign.failed_count
        self.calculate_rates()
        self.save()

    def calculate_rates(self) -> None:
        """Calcula as taxas."""
        if self.sent > 0:
            self.delivery_rate = round((self.delivered / self.sent) * 100, 2)
        else:
            self.delivery_rate = 0

        if self.delivered > 0:
            self.read_rate = round((self.read / self.delivered) * 100, 2)
        else:
            self.read_rate = 0

        if self.total_recipients > 0:
            self.failure_rate = round((self.failed / self.total_recipients) * 100, 2)
        else:
            self.failure_rate = 0

    def calculate_avg_delivery_time(self) -> None:
        """Calcula o tempo médio de entrega."""
        from django.db.models import Avg, F
        from apps.campaigns.models import CampaignRecipient

        avg_time = CampaignRecipient.objects.filter(
            campaign=self.campaign,
            sent_at__isnull=False,
            delivered_at__isnull=False
        ).annotate(
            delivery_time=F('delivered_at') - F('sent_at')
        ).aggregate(
            avg_delivery=Avg('delivery_time')
        )['avg_delivery']

        if avg_time:
            self.avg_delivery_time_seconds = int(avg_time.total_seconds())
        else:
            self.avg_delivery_time_seconds = None
