from django.db import models
from django.contrib.auth import get_user_model
from core.models import BaseModel


User = get_user_model()


class TeamMember(BaseModel):
    """Gerencia membros da equipe com diferentes níveis de acesso"""
    
    ROLE_CHOICES = [
        ('admin', 'Administrador do Tenant'),
        ('coordinator', 'Coordenador'), 
        ('operator', 'Operador'),
        ('analyst', 'Analista'),
        ('volunteer', 'Voluntário'),
    ]
    
    DEPARTMENT_CHOICES = [
        ('political', 'Político'),
        ('communication', 'Comunicação'),
        ('mobilization', 'Mobilização'),
        ('data', 'Dados e Análise'),
        ('finance', 'Financeiro'),
        ('volunteers', 'Voluntariado'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='Usuário',
        related_name='team_memberships'
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='volunteer',
        verbose_name='Função'
    )
    department = models.CharField(
        max_length=50, 
        choices=DEPARTMENT_CHOICES, 
        blank=True,
        verbose_name='Departamento'
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name='Ativo'
    )
    notes = models.TextField(
        blank=True, 
        verbose_name='Observações'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_team_members',
        verbose_name='Criado por'
    )
    
    class Meta:
        verbose_name = 'Membro da Equipe'
        verbose_name_plural = 'Membros da Equipe'
        ordering = ['user__first_name', 'user__last_name']
        unique_together = ['user']  # Um usuário só tem um role por tenant
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"
    
    @property
    def display_name(self):
        """Nome formatado para exibição"""
        return self.user.get_full_name() or self.user.email
    
    @property
    def is_admin_role(self):
        """Verifica se role tem acesso administrativo"""
        return self.role in ['admin', 'coordinator']

    @property
    def can_manage_campaigns(self):
        """Verifica se pode gerenciar campanhas"""
        return self.role in ['admin', 'coordinator', 'operator']

    @property
    def can_view_data(self):
        """Verifica se pode visualizar dados"""
        return self.role in ['admin', 'coordinator', 'operator', 'analyst']

    @property
    def pending(self):
        """Verifica se o membro está pendente (ainda não trocou a senha)"""
        return self.user.force_password_change