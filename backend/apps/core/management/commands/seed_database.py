"""
Management command para popular banco de dados com dados iniciais básicos.

Este comando cria:
1. Planos de assinatura (se não existirem)
2. Tags do sistema (Lead, Apoiador, Blacklist) para todos os tenants

Uso:
    python manage.py seed_database              # Cria tudo
    python manage.py seed_database --dry-run     # Simula
"""

import sys
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django_tenants.utils import schema_context

from apps.tenants.models import Client, Domain, Plan
from apps.supporters.models import Tag

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Popula banco de dados com planos e tags do sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a execução sem salvar alterações',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        self.stdout.write('='*80)
        self.stdout.write('SEED BANCO DE DADOS - VoxPop')
        self.stdout.write('='*80)
        self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  MODO DRY-RUN - Nenhuma alteração será salva'))
            self.stdout.write('')

        # Passo 1: Criar planos de assinatura
        self._create_plans(dry_run)

        # Passo 2: Criar tenant public + domínio localhost
        self._create_public_tenant(dry_run)

        # Passo 3: Criar tags do sistema para todos os tenants
        self._create_system_tags(dry_run)

        self.stdout.write('')
        self.stdout.write('='*80)
        self.stdout.write('✓ Seed concluído!')
        self.stdout.write('='*80)

        if dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Execute sem --dry-run para aplicar alterações'))

    def _create_public_tenant(self, dry_run=False):
        """Cria o tenant public e domínio localhost para o schema público."""
        self.stdout.write('\n🌐 Configurando tenant public...')

        if Client.objects.filter(schema_name='public').exists():
            self.stdout.write('   ⏭️  Tenant public já existe')
        else:
            if not dry_run:
                plan = Plan.objects.first()
                Client.objects.create(
                    schema_name='public',
                    name='VoxPop Platform',
                    slug='public',
                    plan=plan,
                    is_active=True,
                )
            self.stdout.write('   ✅ Tenant public criado')

        if Domain.objects.filter(domain='localhost').exists():
            self.stdout.write('   ⏭️  Domínio localhost já existe')
        else:
            if not dry_run:
                public_tenant = Client.objects.get(schema_name='public')
                Domain.objects.create(
                    domain='localhost',
                    tenant=public_tenant,
                    is_primary=True,
                )
            self.stdout.write('   ✅ Domínio localhost criado')

    def _create_plans(self, dry_run=False):
        """Cria planos de assinatura se não existirem."""
        self.stdout.write('\n📦 Criando planos de assinatura...')

        plans_data = [
            {
                'name': 'Básico',
                'slug': 'basic',
                'description': 'Plano básico para pequenas campanhas',
                'max_supporters': 1000,
                'max_messages_month': 5000,
                'max_campaigns': 10,
                'max_whatsapp_sessions': 1,
                'price': 99.90,
                'is_active': True,
            },
            {
                'name': 'Profissional',
                'slug': 'professional',
                'description': 'Plano profissional para campanhas médias',
                'max_supporters': 10000,
                'max_messages_month': 50000,
                'max_campaigns': 50,
                'max_whatsapp_sessions': 3,
                'price': 299.90,
                'is_active': True,
            },
            {
                'name': 'Enterprise',
                'slug': 'enterprise',
                'description': 'Plano enterprise para grandes operações',
                'max_supporters': 100000,
                'max_messages_month': 500000,
                'max_campaigns': 200,
                'max_whatsapp_sessions': 10,
                'price': 999.90,
                'is_active': True,
            },
        ]

        created_count = 0
        for plan_data in plans_data:
            slug = plan_data['slug']
            if Plan.objects.filter(slug=slug).exists():
                self.stdout.write(f'   ⏭️  Plano "{slug}" já existe')
            else:
                if not dry_run:
                    Plan.objects.create(**plan_data)
                self.stdout.write(f'   ✅ Plano "{slug}" criado')
                created_count += 1

        if created_count > 0:
            self.stdout.write(f'   {created_count} planos criados')
        else:
            self.stdout.write('   Nenhum plano criado (já existiam)')

    def _create_system_tags(self, dry_run=False):
        """Cria tags do sistema para todos os tenants."""
        self.stdout.write('\n🏷️ Criando tags do sistema...')

        tenants = Client.objects.all()
        tenant_count = tenants.count()

        if tenant_count == 0:
            self.stdout.write(self.style.WARNING('   ⚠️  Nenhum tenant encontrado - crie tenants primeiro'))
            return

        self.stdout.write(f'   Encontrados {tenant_count} tenants')

        tags_data = [
            {
                'name': 'Lead',
                'slug': 'lead',
                'color': '#3b82f6',
                'description': 'Contato inicial que ainda não é apoiador',
                'is_system': True,
                'is_active': True,
            },
            {
                'name': 'Apoiador',
                'slug': 'apoiaador',
                'color': '#22c55e',
                'description': 'Apoiador confirmado e engajado',
                'is_system': True,
                'is_active': True,
            },
            {
                'name': 'Blacklist',
                'slug': 'blacklist',
                'color': '#ef4444',
                'description': 'Contato que não deve ser comunicado',
                'is_system': True,
                'is_active': True,
            },
        ]

        total_created = 0

        for tenant in tenants:
            self.stdout.write(f'\n   Tenant: {tenant.name} (schema: {tenant.schema_name})')

            with schema_context(tenant.schema_name):
                for tag_data in tags_data:
                    slug = tag_data['slug']
                    if Tag.objects.filter(slug=slug, is_system=True).exists():
                        self.stdout.write(f'      ⏭️  Tag "{slug}" já existe')
                    else:
                        if not dry_run:
                            Tag.objects.create(**tag_data)
                        self.stdout.write(f'      ✅ Tag "{tag_data["name"]}" criada')
                        total_created += 1

        if total_created > 0:
            self.stdout.write(f'\n   {total_created} tags criadas no total')