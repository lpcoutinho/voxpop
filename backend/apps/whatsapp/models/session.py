"""
WhatsApp Session model for Evolution API integration.
"""
from django.db import models

from core.models import BaseModel


class WhatsAppSession(BaseModel):
    """
    Sessão/Instância do WhatsApp via Evolution API.
    Cada sessão representa uma conexão ativa com o WhatsApp.
    """

    class Status(models.TextChoices):
        DISCONNECTED = 'disconnected', 'Desconectado'
        CONNECTING = 'connecting', 'Conectando'
        CONNECTED = 'connected', 'Conectado'
        BANNED = 'banned', 'Banido'

    name = models.CharField(
        max_length=100,
        verbose_name='Nome da Sessão',
        help_text='Nome amigável para identificar a sessão'
    )
    instance_name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nome da Instância',
        help_text='Nome único da instância na Evolution API'
    )

    # Status da conexão
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DISCONNECTED,
        verbose_name='Status'
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Número Conectado',
        help_text='Número do WhatsApp conectado à sessão'
    )

    # Access Token (Evolution API)
    access_token = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Access Token',
        help_text='Token de acesso da instância na Evolution API'
    )

    # Webhook URL configurado
    webhook_url = models.URLField(
        blank=True,
        verbose_name='URL do Webhook',
        help_text='URL configurada para receber eventos'
    )

    # Limites diários
    daily_message_limit = models.PositiveIntegerField(
        default=1000,
        verbose_name='Limite Diário de Mensagens'
    )
    messages_sent_today = models.PositiveIntegerField(
        default=0,
        verbose_name='Mensagens Enviadas Hoje'
    )
    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Última Mensagem em'
    )

    # Health check
    last_health_check = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Último Health Check'
    )
    is_healthy = models.BooleanField(
        default=False,
        verbose_name='Está Saudável'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    class Meta:
        verbose_name = 'Sessão WhatsApp'
        verbose_name_plural = 'Sessões WhatsApp'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.status})"

    @property
    def is_connected(self) -> bool:
        """Verifica se a sessão está conectada."""
        return self.status == self.Status.CONNECTED

    @property
    def can_send_messages(self) -> bool:
        """Verifica se pode enviar mensagens."""
        return (
            self.is_active
            and self.is_connected
            and self.messages_sent_today < self.daily_message_limit
        )

    @property
    def remaining_messages_today(self) -> int:
        """Retorna quantas mensagens ainda podem ser enviadas hoje."""
        return max(0, self.daily_message_limit - self.messages_sent_today)

    def reset_daily_counter(self) -> None:
        """Reseta o contador diário de mensagens."""
        self.messages_sent_today = 0
        self.save(update_fields=['messages_sent_today', 'updated_at'])

    def increment_message_count(self) -> None:
        """Incrementa o contador de mensagens enviadas."""
        from django.utils import timezone
        self.messages_sent_today += 1
        self.last_message_at = timezone.now()
        self.save(update_fields=['messages_sent_today', 'last_message_at', 'updated_at'])
