"""
Import Job model for bulk supporter imports.
"""
from django.db import models

from core.models import BaseModel


class ImportJob(BaseModel):
    """
    Job de importação em massa de apoiadores.
    Rastreia progresso e erros durante importação.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendente'
        PROCESSING = 'processing', 'Processando'
        COMPLETED = 'completed', 'Concluído'
        FAILED = 'failed', 'Falhou'
        CANCELLED = 'cancelled', 'Cancelado'

    file_name = models.CharField(
        max_length=255,
        verbose_name='Nome do Arquivo'
    )
    file_path = models.CharField(
        max_length=500,
        verbose_name='Caminho do Arquivo'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Status'
    )

    # Contadores de progresso
    total_rows = models.PositiveIntegerField(
        default=0,
        verbose_name='Total de Linhas'
    )
    processed_rows = models.PositiveIntegerField(
        default=0,
        verbose_name='Linhas Processadas'
    )
    success_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Sucessos'
    )
    error_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Erros'
    )
    skipped_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Ignorados',
        help_text='Registros ignorados (duplicados, etc)'
    )

    # Log de erros
    errors_log = models.JSONField(
        default=list,
        verbose_name='Log de Erros',
        help_text='Lista de erros encontrados durante importação'
    )

    # Mapeamento de colunas
    column_mapping = models.JSONField(
        default=dict,
        verbose_name='Mapeamento de Colunas',
        help_text='Correspondência entre colunas do arquivo e campos do modelo'
    )

    # Tags a aplicar automaticamente
    auto_tags = models.ManyToManyField(
        'supporters.Tag',
        blank=True,
        related_name='import_jobs',
        verbose_name='Tags Automáticas',
        help_text='Tags a serem aplicadas automaticamente aos apoiadores importados'
    )

    # Timestamps
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Iniciado em'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Concluído em'
    )

    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='import_jobs',
        verbose_name='Criado por'
    )

    class Meta:
        verbose_name = 'Job de Importação'
        verbose_name_plural = 'Jobs de Importação'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.file_name} ({self.status})"

    @property
    def progress_percentage(self) -> float:
        """Retorna a porcentagem de progresso."""
        if self.total_rows == 0:
            return 0.0
        return round((self.processed_rows / self.total_rows) * 100, 2)

    @property
    def is_completed(self) -> bool:
        """Verifica se o job foi concluído."""
        return self.status in [self.Status.COMPLETED, self.Status.FAILED, self.Status.CANCELLED]

    @property
    def duration_seconds(self) -> int | None:
        """Retorna a duração em segundos."""
        if not self.started_at:
            return None
        end_time = self.completed_at or self.updated_at
        return int((end_time - self.started_at).total_seconds())

    def mark_as_processing(self) -> None:
        """Marca o job como em processamento."""
        from django.utils import timezone
        self.status = self.Status.PROCESSING
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at', 'updated_at'])

    def mark_as_completed(self) -> None:
        """Marca o job como concluído."""
        from django.utils import timezone
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])

    def mark_as_failed(self, error: str = '') -> None:
        """Marca o job como falhou."""
        from django.utils import timezone
        self.status = self.Status.FAILED
        self.completed_at = timezone.now()
        if error:
            self.errors_log.append({'type': 'fatal', 'message': error})
        self.save(update_fields=['status', 'completed_at', 'errors_log', 'updated_at'])

    def add_error(self, row: int, field: str, message: str) -> None:
        """Adiciona um erro ao log."""
        self.errors_log.append({
            'row': row,
            'field': field,
            'message': message
        })
        self.error_count += 1
        self.processed_rows += 1
        self.save(update_fields=['errors_log', 'error_count', 'processed_rows', 'updated_at'])

    def increment_success(self) -> None:
        """Incrementa contador de sucesso."""
        self.success_count += 1
        self.processed_rows += 1
        self.save(update_fields=['success_count', 'processed_rows', 'updated_at'])

    def increment_skipped(self) -> None:
        """Incrementa contador de ignorados."""
        self.skipped_count += 1
        self.processed_rows += 1
        self.save(update_fields=['skipped_count', 'processed_rows', 'updated_at'])
