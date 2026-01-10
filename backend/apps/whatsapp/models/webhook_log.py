"""
Webhook Log model for tracking Evolution API events.
"""
from django.db import models

from core.models import BaseModel


class WebhookLog(BaseModel):
    """
    Log de webhooks recebidos da Evolution API.
    Armazena todos os eventos para processamento e auditoria.
    """

    class EventType(models.TextChoices):
        QRCODE_UPDATED = 'qrcode.updated', 'QR Code Atualizado'
        CONNECTION_UPDATE = 'connection.update', 'Atualização de Conexão'
        MESSAGES_UPSERT = 'messages.upsert', 'Nova Mensagem'
        MESSAGES_UPDATE = 'messages.update', 'Atualização de Mensagem'
        SEND_MESSAGE = 'send.message', 'Mensagem Enviada'

    session = models.ForeignKey(
        'whatsapp.WhatsAppSession',
        on_delete=models.CASCADE,
        related_name='webhook_logs',
        verbose_name='Sessão'
    )
    event_type = models.CharField(
        max_length=50,
        verbose_name='Tipo de Evento',
        help_text='Tipo do evento recebido da Evolution API'
    )

    # Payload completo
    payload = models.JSONField(
        verbose_name='Payload',
        help_text='Payload JSON completo do webhook'
    )

    # Processamento
    processed = models.BooleanField(
        default=False,
        verbose_name='Processado'
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Processado em'
    )
    error = models.TextField(
        blank=True,
        verbose_name='Erro',
        help_text='Mensagem de erro se o processamento falhou'
    )

    class Meta:
        verbose_name = 'Log de Webhook'
        verbose_name_plural = 'Logs de Webhook'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session', 'event_type']),
            models.Index(fields=['processed', 'created_at']),
            models.Index(fields=['event_type', 'processed']),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.session.name} ({self.created_at})"

    def mark_as_processed(self, error: str = '') -> None:
        """Marca o webhook como processado."""
        from django.utils import timezone
        self.processed = True
        self.processed_at = timezone.now()
        self.error = error
        self.save(update_fields=['processed', 'processed_at', 'error', 'updated_at'])
