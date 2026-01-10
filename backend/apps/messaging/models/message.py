"""
Message model for tracking individual messages.
"""
from django.db import models

from core.models import BaseModel


class Message(BaseModel):
    """
    Mensagem individual enviada via WhatsApp.
    Rastreia status de entrega e leitura.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendente'
        QUEUED = 'queued', 'Na Fila'
        SENT = 'sent', 'Enviada'
        DELIVERED = 'delivered', 'Entregue'
        READ = 'read', 'Lida'
        FAILED = 'failed', 'Falhou'

    # Destinatário
    phone = models.CharField(
        max_length=20,
        verbose_name='Telefone',
        help_text='Número do destinatário no formato E.164'
    )
    supporter = models.ForeignKey(
        'supporters.Supporter',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
        verbose_name='Apoiador'
    )

    # Conteúdo
    template = models.ForeignKey(
        'messaging.MessageTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
        verbose_name='Template'
    )
    content = models.TextField(
        verbose_name='Conteúdo',
        help_text='Conteúdo renderizado da mensagem'
    )
    message_type = models.CharField(
        max_length=20,
        verbose_name='Tipo de Mensagem'
    )
    media_url = models.URLField(
        blank=True,
        verbose_name='URL da Mídia'
    )

    # Status e tracking
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Status'
    )

    # IDs externos (Evolution API)
    external_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name='ID Externo',
        help_text='ID da mensagem na Evolution API'
    )
    whatsapp_message_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='ID WhatsApp',
        help_text='ID da mensagem no WhatsApp'
    )

    # Sessão usada
    whatsapp_session = models.ForeignKey(
        'whatsapp.WhatsAppSession',
        on_delete=models.SET_NULL,
        null=True,
        related_name='messages',
        verbose_name='Sessão WhatsApp'
    )

    # Campanha (se parte de uma)
    campaign = models.ForeignKey(
        'campaigns.Campaign',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
        verbose_name='Campanha'
    )

    # Timestamps de status
    queued_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Enfileirada em'
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Enviada em'
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Entregue em'
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Lida em'
    )
    failed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Falhou em'
    )

    # Erro
    error_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Código de Erro'
    )
    error_message = models.TextField(
        blank=True,
        verbose_name='Mensagem de Erro'
    )

    # Tentativas
    retry_count = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Tentativas'
    )

    class Meta:
        verbose_name = 'Mensagem'
        verbose_name_plural = 'Mensagens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['external_id']),
            models.Index(fields=['phone', 'status']),
            models.Index(fields=['campaign', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"Mensagem para {self.phone} ({self.status})"

    @property
    def is_delivered(self) -> bool:
        """Verifica se a mensagem foi entregue."""
        return self.status in [self.Status.DELIVERED, self.Status.READ]

    @property
    def is_failed(self) -> bool:
        """Verifica se a mensagem falhou."""
        return self.status == self.Status.FAILED

    @property
    def can_retry(self) -> bool:
        """Verifica se a mensagem pode ser reenviada."""
        return self.is_failed and self.retry_count < 3

    def mark_as_queued(self) -> None:
        """Marca a mensagem como enfileirada."""
        from django.utils import timezone
        self.status = self.Status.QUEUED
        self.queued_at = timezone.now()
        self.save(update_fields=['status', 'queued_at', 'updated_at'])

    def mark_as_sent(self, external_id: str = '', whatsapp_id: str = '') -> None:
        """Marca a mensagem como enviada."""
        from django.utils import timezone
        self.status = self.Status.SENT
        self.sent_at = timezone.now()
        if external_id:
            self.external_id = external_id
        if whatsapp_id:
            self.whatsapp_message_id = whatsapp_id
        self.save(update_fields=[
            'status', 'sent_at', 'external_id', 'whatsapp_message_id', 'updated_at'
        ])

    def mark_as_delivered(self) -> None:
        """Marca a mensagem como entregue."""
        from django.utils import timezone
        self.status = self.Status.DELIVERED
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at', 'updated_at'])

    def mark_as_read(self) -> None:
        """Marca a mensagem como lida."""
        from django.utils import timezone
        self.status = self.Status.READ
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at', 'updated_at'])

    def mark_as_failed(self, error_code: str = '', error_message: str = '') -> None:
        """Marca a mensagem como falhou."""
        from django.utils import timezone
        self.status = self.Status.FAILED
        self.failed_at = timezone.now()
        self.error_code = error_code
        self.error_message = error_message
        self.save(update_fields=[
            'status', 'failed_at', 'error_code', 'error_message', 'updated_at'
        ])
