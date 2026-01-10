"""
Domain model for VoxPop multi-tenancy.
Each tenant can have one or more domains pointing to it.
"""
from django_tenants.models import DomainMixin


class Domain(DomainMixin):
    """
    Domínios associados ao tenant.

    Exemplos:
        - Produção: campanha-joao.voxpop.com.br
        - Desenvolvimento: joao.localhost
    """

    class Meta:
        verbose_name = 'Domínio'
        verbose_name_plural = 'Domínios'

    def __str__(self):
        return self.domain
