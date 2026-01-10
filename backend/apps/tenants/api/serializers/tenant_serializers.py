from django.utils.text import slugify
from rest_framework import serializers

from apps.tenants.models import Client, Plan


class TenantSerializer(serializers.ModelSerializer):
    """Serializer para visualização de tenant."""
    plan_name = serializers.CharField(source='plan.name', read_only=True)

    class Meta:
        model = Client
        fields = [
            'id',
            'name',
            'slug',
            'document',
            'plan',
            'plan_name',
            'email',
            'phone',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'slug', 'is_active', 'created_at']


class TenantInputSerializer(serializers.Serializer):
    """Input para dados do tenant."""
    name = serializers.CharField(max_length=255)
    document = serializers.CharField(max_length=18)
    plan_id = serializers.IntegerField()
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_document(self, value):
        # Remove caracteres especiais
        cleaned = ''.join(filter(str.isdigit, value))
        if len(cleaned) != 14:
            raise serializers.ValidationError('CNPJ deve conter 14 dígitos.')
        if Client.objects.filter(document=value).exists():
            raise serializers.ValidationError('CNPJ já cadastrado.')
        return value

    def validate_plan_id(self, value):
        if not Plan.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError('Plano inválido ou inativo.')
        return value

    def validate_name(self, value):
        slug = slugify(value)
        if Client.objects.filter(slug=slug).exists():
            raise serializers.ValidationError(
                'Já existe uma organização com nome similar.'
            )
        return value


class OwnerInputSerializer(serializers.Serializer):
    """Input para dados do usuário owner."""
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)


class TenantCreateSerializer(serializers.Serializer):
    """
    Serializer para criação de tenant com owner.
    Usado no endpoint de registro.
    """
    tenant = TenantInputSerializer()
    owner = OwnerInputSerializer()
    domain = serializers.CharField(
        max_length=253,
        help_text='Subdomínio desejado (ex: minha-campanha)'
    )

    def validate_domain(self, value):
        # Valida formato do domínio
        from apps.tenants.models import Domain

        # Remove espaços e converte para lowercase
        value = value.strip().lower()

        # Verifica se já existe
        if Domain.objects.filter(domain__iexact=value).exists():
            raise serializers.ValidationError('Este domínio já está em uso.')

        return value
