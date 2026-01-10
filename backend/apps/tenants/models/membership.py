"""
TenantMembership model for user-tenant relationships.
"""
from django.conf import settings
from django.db import models


class TenantMembership(models.Model):
    """
    Relação entre usuários e tenants com roles.
    Um usuário pode pertencer a múltiplos tenants com diferentes papéis.
    """

    class Role(models.TextChoices):
        OWNER = 'owner', 'Proprietário'
        ADMIN = 'admin', 'Administrador'
        OPERATOR = 'operator', 'Operador'
        VIEWER = 'viewer', 'Visualizador'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name='Usuário'
    )
    tenant = models.ForeignKey(
        'Client',
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name='Tenant'
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
        verbose_name='Papel'
    )

    # Controle
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Membro do Tenant'
        verbose_name_plural = 'Membros do Tenant'
        unique_together = ['user', 'tenant']
        ordering = ['tenant', 'role', 'user']

    def __str__(self):
        return f"{self.user.email} - {self.tenant.name} ({self.get_role_display()})"

    @property
    def is_owner(self) -> bool:
        return self.role == self.Role.OWNER

    @property
    def is_admin(self) -> bool:
        return self.role in [self.Role.OWNER, self.Role.ADMIN]

    @property
    def can_edit(self) -> bool:
        return self.role in [self.Role.OWNER, self.Role.ADMIN, self.Role.OPERATOR]
