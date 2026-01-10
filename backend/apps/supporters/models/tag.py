"""
Tag models for supporter segmentation.
"""
from django.db import models
from django.utils.text import slugify

from core.models import BaseModel


class Tag(BaseModel):
    """
    Tag para segmentação de apoiadores.
    Permite categorizar e filtrar apoiadores.
    """

    # Tags de sistema (criadas automaticamente por tenant)
    SYSTEM_TAGS = {
        'lead': {
            'name': 'Lead',
            'color': '#3B82F6',
            'description': 'Contato inicial - ainda não é apoiador'
        },
        'apoiador': {
            'name': 'Apoiador',
            'color': '#22C55E',
            'description': 'Contato engajado - apoiador confirmado'
        },
        'blacklist': {
            'name': 'Blacklist',
            'color': '#EF4444',
            'description': 'Não contatar - excluído de campanhas'
        },
    }

    name = models.CharField(
        max_length=50,
        verbose_name='Nome'
    )
    slug = models.SlugField(
        max_length=50,
        blank=True,
        verbose_name='Slug',
        help_text='Identificador único (gerado automaticamente)'
    )
    color = models.CharField(
        max_length=7,
        default='#6366f1',
        verbose_name='Cor',
        help_text='Cor em formato hexadecimal (#RRGGBB)'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativa'
    )
    is_system = models.BooleanField(
        default=False,
        verbose_name='Tag de Sistema',
        help_text='Tags de sistema não podem ser deletadas'
    )

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['-is_system', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['name'],
                name='unique_tag_name_per_tenant'
            ),
            models.UniqueConstraint(
                fields=['slug'],
                condition=models.Q(slug__isnull=False) & ~models.Q(slug=''),
                name='unique_tag_slug_per_tenant'
            ),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Gera slug automaticamente se não existir."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Impede deleção de tags de sistema."""
        if self.is_system:
            raise ValueError(f"Tag de sistema '{self.name}' não pode ser deletada.")
        super().delete(*args, **kwargs)

    @property
    def supporters_count(self) -> int:
        """Retorna a quantidade de apoiadores com esta tag."""
        return self.supporter_tags.count()

    @classmethod
    def create_system_tags(cls):
        """Cria as tags de sistema para o tenant atual."""
        created_tags = []
        for slug, data in cls.SYSTEM_TAGS.items():
            tag, created = cls.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': data['name'],
                    'color': data['color'],
                    'description': data['description'],
                    'is_system': True,
                }
            )
            if created:
                created_tags.append(tag)
        return created_tags

    @classmethod
    def get_lead_tag(cls):
        """Retorna a tag Lead do tenant atual."""
        return cls.objects.filter(slug='lead', is_system=True).first()

    @classmethod
    def get_supporter_tag(cls):
        """Retorna a tag Apoiador do tenant atual."""
        return cls.objects.filter(slug='apoiador', is_system=True).first()

    @classmethod
    def get_blacklist_tag(cls):
        """Retorna a tag Blacklist do tenant atual."""
        return cls.objects.filter(slug='blacklist', is_system=True).first()


class SupporterTag(BaseModel):
    """
    Relação M2M entre Supporter e Tag.
    Tabela intermediária para controle adicional.
    """

    supporter = models.ForeignKey(
        'supporters.Supporter',
        on_delete=models.CASCADE,
        related_name='supporter_tags',
        verbose_name='Apoiador'
    )
    tag = models.ForeignKey(
        'supporters.Tag',
        on_delete=models.CASCADE,
        related_name='supporter_tags',
        verbose_name='Tag'
    )

    class Meta:
        verbose_name = 'Tag do Apoiador'
        verbose_name_plural = 'Tags dos Apoiadores'
        unique_together = ['supporter', 'tag']

    def __str__(self):
        return f"{self.supporter.name} - {self.tag.name}"
