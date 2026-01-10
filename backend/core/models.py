"""
Base models for VoxPop.
"""
from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model with common fields.
    All tenant-specific models should inherit from this.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']


class SoftDeleteManager(models.Manager):
    """Manager that filters out soft-deleted objects."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteModel(BaseModel):
    """
    Abstract model with soft delete functionality.
    Objects are marked as deleted instead of being actually deleted.
    """
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Deletado em'
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Includes deleted objects

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Soft delete the object."""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at', 'updated_at'])

    def hard_delete(self, using=None, keep_parents=False):
        """Actually delete the object from database."""
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """Restore a soft-deleted object."""
        self.deleted_at = None
        self.save(update_fields=['deleted_at', 'updated_at'])

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
