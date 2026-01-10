"""
Segment model for dynamic supporter filtering.
"""
from django.db import models

from core.models import BaseModel


class Segment(BaseModel):
    """
    Segmento dinâmico baseado em filtros.
    Permite criar grupos de apoiadores com critérios específicos.
    """

    name = models.CharField(
        max_length=100,
        verbose_name='Nome do Segmento'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )

    # Filtros como JSON
    # Exemplo: {"city": "São Paulo", "tags": [1,2], "age_min": 18, "age_max": 65}
    filters = models.JSONField(
        default=dict,
        verbose_name='Filtros',
        help_text='Critérios de filtro em formato JSON'
    )

    # Cache de contagem
    cached_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Contagem (Cache)'
    )
    cached_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Cache Atualizado em'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='segments',
        verbose_name='Criado por'
    )

    class Meta:
        verbose_name = 'Segmento'
        verbose_name_plural = 'Segmentos'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.cached_count} apoiadores)"

    def get_supporters_queryset(self):
        """
        Retorna QuerySet de apoiadores baseado nos filtros.
        """
        from apps.supporters.models import Supporter, Tag

        qs = Supporter.objects.filter(whatsapp_opt_in=True)

        filters = self.filters or {}

        # Filtro por status do contato (Lead, Apoiador, Blacklist)
        if contact_status := filters.get('contact_status'):
            tag_name_map = {
                'lead': 'Lead',
                'apoiador': 'Apoiador',
                'blacklist': 'Blacklist'
            }
            tag_name = tag_name_map.get(contact_status)
            if tag_name:
                try:
                    system_tag = Tag.objects.get(name=tag_name, is_system=True)
                    qs = qs.filter(tags=system_tag)
                except Tag.DoesNotExist:
                    pass

        # Filtro por cidade
        if city := filters.get('city'):
            qs = qs.filter(city__iexact=city)

        # Filtro por estado
        if state := filters.get('state'):
            qs = qs.filter(state__iexact=state)

        # Filtro por bairro
        if neighborhood := filters.get('neighborhood'):
            qs = qs.filter(neighborhood__icontains=neighborhood)

        # Filtro por gênero
        if gender := filters.get('gender'):
            qs = qs.filter(gender=gender)

        # Filtro por tags (any)
        if tag_ids := filters.get('tags'):
            qs = qs.filter(tags__id__in=tag_ids).distinct()

        # Filtro por tags (all - precisa ter todas)
        if tag_ids_all := filters.get('tags_all'):
            for tag_id in tag_ids_all:
                qs = qs.filter(tags__id=tag_id)

        # Filtro por idade mínima
        if age_min := filters.get('age_min'):
            from datetime import date, timedelta
            max_birth_date = date.today() - timedelta(days=age_min * 365)
            qs = qs.filter(birth_date__lte=max_birth_date)

        # Filtro por idade máxima
        if age_max := filters.get('age_max'):
            from datetime import date, timedelta
            min_birth_date = date.today() - timedelta(days=(age_max + 1) * 365)
            qs = qs.filter(birth_date__gt=min_birth_date)

        # Filtro por zona eleitoral
        if zone := filters.get('electoral_zone'):
            qs = qs.filter(electoral_zone=zone)

        # Filtro por seção eleitoral
        if section := filters.get('electoral_section'):
            qs = qs.filter(electoral_section=section)

        # Filtro por origem
        if source := filters.get('source'):
            qs = qs.filter(source=source)

        return qs

    def update_cached_count(self) -> int:
        """Atualiza a contagem em cache."""
        from django.utils import timezone
        count = self.get_supporters_queryset().count()
        self.cached_count = count
        self.cached_at = timezone.now()
        self.save(update_fields=['cached_count', 'cached_at', 'updated_at'])
        return count

    def get_sample(self, limit: int = 10):
        """Retorna uma amostra de apoiadores do segmento."""
        return self.get_supporters_queryset()[:limit]
