"""
Supporter model for political contacts management.
"""
from django.db import models

from core.models import SoftDeleteModel


class Supporter(SoftDeleteModel):
    """
    Apoiador/Contato político.
    Armazena informações de contato e dados para segmentação.
    """

    class Gender(models.TextChoices):
        MALE = 'M', 'Masculino'
        FEMALE = 'F', 'Feminino'
        OTHER = 'O', 'Outro'

    class Source(models.TextChoices):
        IMPORT = 'import', 'Importação'
        FORM = 'form', 'Formulário'
        MANUAL = 'manual', 'Cadastro Manual'
        API = 'api', 'API'

    # Dados básicos
    name = models.CharField(
        max_length=255,
        verbose_name='Nome Completo'
    )
    phone = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Telefone',
        help_text='Número no formato E.164 (+5511999999999)'
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='E-mail'
    )
    cpf = models.CharField(
        max_length=14,
        blank=True,
        verbose_name='CPF'
    )

    # Dados de localização
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Cidade'
    )
    neighborhood = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Bairro'
    )
    state = models.CharField(
        max_length=2,
        blank=True,
        verbose_name='Estado'
    )
    zip_code = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='CEP'
    )

    # Dados eleitorais
    electoral_zone = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Zona Eleitoral'
    )
    electoral_section = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Seção Eleitoral'
    )

    # Segmentação demográfica
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Nascimento'
    )
    gender = models.CharField(
        max_length=1,
        choices=Gender.choices,
        blank=True,
        verbose_name='Gênero'
    )

    # Opt-in WhatsApp
    whatsapp_opt_in = models.BooleanField(
        default=False,
        verbose_name='Opt-in WhatsApp',
        help_text='Consentiu receber mensagens via WhatsApp'
    )
    opt_in_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data do Opt-in'
    )

    # Metadados
    source = models.CharField(
        max_length=50,
        choices=Source.choices,
        default=Source.MANUAL,
        verbose_name='Origem'
    )
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Dados Extras',
        help_text='Campos adicionais em formato JSON'
    )

    # Tags (M2M através de SupporterTag)
    tags = models.ManyToManyField(
        'supporters.Tag',
        through='supporters.SupporterTag',
        related_name='supporters',
        blank=True,
        verbose_name='Tags'
    )

    class Meta:
        verbose_name = 'Apoiador'
        verbose_name_plural = 'Apoiadores'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['city', 'neighborhood']),
            models.Index(fields=['state', 'city']),
            models.Index(fields=['whatsapp_opt_in']),
        ]

    def __str__(self):
        return f"{self.name} ({self.phone})"

    @property
    def age(self) -> int | None:
        """Calcula a idade do apoiador."""
        if not self.birth_date:
            return None
        from datetime import date
        today = date.today()
        return (
            today.year - self.birth_date.year -
            ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )

    @property
    def can_receive_messages(self) -> bool:
        """Verifica se o apoiador pode receber mensagens."""
        return self.whatsapp_opt_in and bool(self.phone)

    def get_template_context(self) -> dict:
        """Retorna contexto para renderização de templates."""
        return {
            'name': self.name,
            'first_name': self.name.split()[0] if self.name else '',
            'phone': self.phone,
            'email': self.email or '',
            'city': self.city,
            'neighborhood': self.neighborhood,
            'state': self.state,
            'age': self.age,
            **self.extra_data
        }

    # ===========================================
    # Métodos de Status (Lead/Apoiador/Blacklist)
    # ===========================================

    @property
    def is_lead(self) -> bool:
        """Verifica se o contato é um Lead."""
        return self.tags.filter(slug='lead', is_system=True).exists()

    @property
    def is_supporter_status(self) -> bool:
        """Verifica se o contato é um Apoiador confirmado."""
        return self.tags.filter(slug='apoiador', is_system=True).exists()

    @property
    def is_blacklisted(self) -> bool:
        """Verifica se o contato está na Blacklist."""
        return self.tags.filter(slug='blacklist', is_system=True).exists()

    @property
    def contact_status(self) -> str:
        """Retorna o status atual do contato."""
        if self.is_blacklisted:
            return 'blacklist'
        if self.is_supporter_status:
            return 'apoiador'
        if self.is_lead:
            return 'lead'
        return 'sem_status'

    def promote_to_supporter(self) -> bool:
        """
        Promove o contato de Lead para Apoiador.
        Remove a tag Lead e adiciona a tag Apoiador.
        Retorna True se a promoção foi realizada.
        """
        from apps.supporters.models import Tag

        lead_tag = Tag.get_lead_tag()
        supporter_tag = Tag.get_supporter_tag()

        if not supporter_tag:
            return False

        # Remove tag Lead se existir
        if lead_tag and self.tags.filter(pk=lead_tag.pk).exists():
            self.tags.remove(lead_tag)

        # Adiciona tag Apoiador se não existir
        if not self.tags.filter(pk=supporter_tag.pk).exists():
            self.tags.add(supporter_tag)

        return True

    def demote_to_lead(self) -> bool:
        """
        Demote o contato de Apoiador para Lead.
        Remove a tag Apoiador e adiciona a tag Lead.
        Retorna True se a operação foi realizada.
        """
        from apps.supporters.models import Tag

        lead_tag = Tag.get_lead_tag()
        supporter_tag = Tag.get_supporter_tag()

        if not lead_tag:
            return False

        # Remove tag Apoiador se existir
        if supporter_tag and self.tags.filter(pk=supporter_tag.pk).exists():
            self.tags.remove(supporter_tag)

        # Adiciona tag Lead se não existir
        if not self.tags.filter(pk=lead_tag.pk).exists():
            self.tags.add(lead_tag)

        return True

    def add_to_blacklist(self) -> bool:
        """
        Adiciona o contato à Blacklist.
        Retorna True se a operação foi realizada.
        """
        from apps.supporters.models import Tag

        blacklist_tag = Tag.get_blacklist_tag()

        if not blacklist_tag:
            return False

        if not self.tags.filter(pk=blacklist_tag.pk).exists():
            self.tags.add(blacklist_tag)

        return True

    def remove_from_blacklist(self) -> bool:
        """
        Remove o contato da Blacklist.
        Retorna True se a operação foi realizada.
        """
        from apps.supporters.models import Tag

        blacklist_tag = Tag.get_blacklist_tag()

        if not blacklist_tag:
            return False

        if self.tags.filter(pk=blacklist_tag.pk).exists():
            self.tags.remove(blacklist_tag)

        return True

    def set_as_lead(self) -> bool:
        """
        Define o contato como Lead (usado no cadastro inicial).
        Retorna True se a operação foi realizada.
        """
        from apps.supporters.models import Tag

        lead_tag = Tag.get_lead_tag()

        if not lead_tag:
            return False

        if not self.tags.filter(pk=lead_tag.pk).exists():
            self.tags.add(lead_tag)

        return True
