"""
Message Template model for reusable message content.
"""
from django.db import models

from core.models import SoftDeleteModel


class MessageTemplate(SoftDeleteModel):
    """
    Template de mensagem reutilizável.
    Suporta variáveis dinâmicas como {{name}}, {{city}}.
    """

    class Type(models.TextChoices):
        TEXT = 'text', 'Texto'
        IMAGE = 'image', 'Imagem'
        DOCUMENT = 'document', 'Documento'
        AUDIO = 'audio', 'Áudio'
        VIDEO = 'video', 'Vídeo'

    name = models.CharField(
        max_length=100,
        verbose_name='Nome do Template'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )
    message_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.TEXT,
        verbose_name='Tipo de Mensagem'
    )

    # Conteúdo
    content = models.TextField(
        verbose_name='Conteúdo',
        help_text='Texto da mensagem. Suporta variáveis: {{name}}, {{city}}, etc.'
    )

    # Mídia (se aplicável)
    media_url = models.URLField(
        blank=True,
        verbose_name='URL da Mídia',
        help_text='URL da imagem, documento, áudio ou vídeo'
    )
    media_filename = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Nome do Arquivo'
    )
    media_mimetype = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Tipo MIME'
    )

    # Variáveis disponíveis
    variables = models.JSONField(
        default=list,
        verbose_name='Variáveis',
        help_text='Lista de variáveis disponíveis no template'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='message_templates',
        verbose_name='Criado por'
    )

    class Meta:
        verbose_name = 'Template de Mensagem'
        verbose_name_plural = 'Templates de Mensagem'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.message_type})"

    @property
    def has_media(self) -> bool:
        """Verifica se o template tem mídia."""
        return self.message_type != self.Type.TEXT and bool(self.media_url)

    def extract_variables(self) -> list[str]:
        """Extrai variáveis do conteúdo ({{variable}})."""
        import re
        pattern = r'\{\{(\w+)\}\}'
        return re.findall(pattern, self.content)

    def render(self, context: dict) -> str:
        """Renderiza o template com as variáveis fornecidas."""
        from core.utils import render_template_variables
        return render_template_variables(self.content, context)
