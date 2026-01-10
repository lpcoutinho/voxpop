"""
Custom User model for VoxPop.
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Custom user manager that uses email as the unique identifier."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError('O email é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser deve ter is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model que usa email como identificador único.
    Remove o campo username do AbstractUser.
    """
    username = None
    email = models.EmailField(
        'E-mail',
        unique=True,
    )
    phone = models.CharField(
        'Telefone',
        max_length=20,
        blank=True,
    )
    is_verified = models.BooleanField(
        'E-mail verificado',
        default=False,
    )
    force_password_change = models.BooleanField(
        'Forçar troca de senha',
        default=False,
    )
    avatar = models.URLField(
        'Avatar',
        blank=True,
        null=True,
    )

    # Tenant atual (para facilitar navegação)
    current_tenant = models.ForeignKey(
        'tenants.Client',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_users',
        verbose_name='Tenant atual',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    objects = UserManager()

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['email']

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name or self.email

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.email.split('@')[0]

    def get_tenants(self):
        """Retorna todos os tenants que o usuário tem acesso."""
        from apps.tenants.models import TenantMembership
        return [
            m.tenant for m in TenantMembership.objects.filter(
                user=self, is_active=True
            ).select_related('tenant')
        ]

    def get_membership(self, tenant):
        """Retorna a membership do usuário para um tenant específico."""
        from apps.tenants.models import TenantMembership
        return TenantMembership.objects.filter(
            user=self, tenant=tenant, is_active=True
        ).first()
