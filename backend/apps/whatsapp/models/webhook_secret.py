"""
Modelos para gerenciamento de segredos de webhooks.
"""
import uuid

from django.db import models


class WebhookSecret(models.Model):
    """
    Secret compartilhado entre Django e Evolution API para validação de webhooks.

    Cada instância de WhatsApp pode ter seu próprio secret.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Identificação
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, help_text="Descrição do secret (ex: 'Webhook do Tenant X')")

    # O secret em si (HMAC-SHA256)
    secret_token = models.CharField(max_length=64, unique=True)

    # Controle de ativação
    is_active = models.BooleanField(default=True)

    # Rastreamento
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True=True)

    # Timestamp de última rotação (para rotação de secrets)
    last_rotated_at = models.DateTimeField(null=True, blank=True, help_text="Data da última rotação deste secret")
    rotation_interval_days = models.PositiveIntegerField(default=90, help_text="Dias para rotação (padrão: 90)")

    # Metadados
    last_used_at = models.DateTimeField(null=True, blank=True, help_text="Último uso deste secret")
    usage_count = models.PositiveIntegerField(default=0, help_text="Número de vezes que este secret foi usado")

    class Meta:
        db_table = 'whatsapp_webhook_secrets'
        verbose_name = 'Webhook Secret'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['secret_token']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({'Ativo' if self.is_active else 'Inativo'})"

    def rotate(self):
        """Marca secret como usado e cria novo secret."""
        from .services.webhook_secret_service import WebhookSecretService

        service = WebhookSecretService()
        new_secret = service.rotate_secret(self)
        self.delete()
        return new_secret

    @property
    def is_expired(self):
        """Verifica se o secret expirou baseado na rotação."""
        if not self.last_rotated_at:
            return False

        from django.utils import timezone
        from datetime import timedelta
        expiry_date = self.last_rotated_at + timedelta(days=self.rotation_interval_days)
        return timezone.now() > expiry_date

    @property
    def needs_rotation(self):
        """Verifica se o secret precisa ser rotacionado."""
        if not self.is_active:
            return False

        from django.utils import timezone
        from datetime import timedelta

        # Se nunca foi usado, pode rotacionar
        if not self.last_used_at:
            return True

        # Se foi usado há mais de 90 dias, precisa rotacionar
        if self.last_used_at:
            rotation_threshold = self.last_used_at + timedelta(days=self.rotation_interval_days)
            return timezone.now() > rotation_threshold

        return False


class WebhookSecretUsage(models.Model):
    """
    Registro de uso de secrets por tenant/instância.
    Permite controlar qual secret está sendo usado e quando foi usado pela última vez.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Tenant
    tenant = models.ForeignKey(
        'tenants.Client',
        on_delete=models.CASCADE,
        related_name='secrets',
        db_index=True   # Otimiza queries filtrando por tenant
    )

    # Secret sendo usado
    secret = models.ForeignKey(
        WebhookSecret,
        on_delete=models.CASCADE,
        related_name='usages',
        db_index=True,
    )

    # Qual sessão/instância está usando este secret
    session_name = models.CharField(max_length=100, blank=True, help_text="Nome da sessão/instância (opcional)")

    # Contexto do uso
    context = models.CharField(
        max_length=50,
        blank=True,
        help_text="Contexto do uso (ex: 'webhook-message-handler', 'scheduled-task')"
    )

    # IP de origem da requisição (para segurança)
    ip_address = models.GenericIPAddressField(
        null=True, blank=True,
        help_text="IP de origem da requisição"
    )

    # User agent (browser, API, etc)
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        help_text="User agent da requisição"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'whatsapp_webhook_secret_usage'
        verbose_name = 'Uso de Secret de Webhook'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'secret']),
            models.Index(fields=['session_name']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.secret.name} - {self.context or 'sem contexto'}"
