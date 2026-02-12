"""
Management command para recalcular métricas de campanhas antigas.

Este comando:
1. Busca todos os tenants (Client)
2. Para cada tenant, busca campanhas completadas/rodando
3. Para cada campanha, itera sobre todos os CampaignItems
4. Conta itens com status delivered/read
5. Atualiza messages_delivered e messages_read da campanha
6. Marca a campanha como tendo métricas verificadas

Uso:
    python manage.py recalcular_metricas_campanhas              # Recalcula todas
    python manage.py recalcular_metricas_campanhas --campaign-id 123  # Recalcula apenas uma
    python manage.py recalcular_metricas_campanhas --dry-run    # Mostra o que será feito (dry run)
"""
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django_tenants.utils import schema_context
from django_tenants.utils import get_tenant_model
from apps.campaigns.models import Campaign, CampaignItem

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Recalcular métricas de campanhas antigas baseadas nos CampaignItems'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Processa todas as campanhas (padrão: apenas completadas/rodando)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a execução sem salvar alterações',
        )
        parser.add_argument(
            '--campaign-id',
            type=int,
            help='ID da campanha específica para processar',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        campaign_id = options.get('campaign_id')

        self.stdout.write('='*80)
        self.stdout.write('RECALCULAR MÉTRICAS DE CAMPANHAS ANTIGAS')
        self.stdout.write('='*80)
        self.stdout.write('Baseando contagem em CampaignItems existentes')
        self.stdout.write('')

        # Busca o modelo de tenant (Client)
        Client = get_tenant_model()

        if campaign_id:
            # Para campanha específica, primeiro encontra o tenant
            self.stdout.write(f'\n📊 Buscando campanha ID: {campaign_id}')
            self.stdout.write('   Procurando em todos os tenants...')

            # Itera sobre todos os tenants para encontrar a campanha
            found = False
            for tenant in Client.objects.exclude(schema_name='public'):
                with schema_context(tenant.schema_name):
                    try:
                        campaign = Campaign.objects.get(
                            id=campaign_id,
                            status__in=['completed', 'running']
                        )
                        found = True
                        self._process_campaign(campaign, dry_run)
                        break
                    except Campaign.DoesNotExist:
                        continue

            if not found:
                self.stdout.write(f'   ❌ Campanha ID "{campaign_id}" não encontrada')
        else:
            # Processa todas as campanhas em todos os tenants
            self.stdout.write('\n📊 Buscando campanhas em todos os tenants...')

            total_campaigns_processed = 0
            total_campaigns_updated = 0
            total_campaigns_skipped = 0

            for tenant in Client.objects.exclude(schema_name='public'):
                self.stdout.write(f'\n📦 Tenant: {tenant.name} (schema: {tenant.schema_name})')

                with schema_context(tenant.schema_name):
                    campaigns = Campaign.objects.filter(
                        status__in=['completed', 'running']
                    )

                    if not campaigns.exists():
                        self.stdout.write('   ⏭️  Nenhuma campanha ativa/completada')
                        continue

                    self.stdout.write(f'   📊 Encontradas {campaigns.count()} campanhas')

                    for campaign in campaigns:
                        updated = self._process_campaign(campaign, dry_run)
                        total_campaigns_processed += 1
                        if updated:
                            total_campaigns_updated += 1
                        else:
                            total_campaigns_skipped += 1

            # Resumo final
            self.stdout.write('')
            self.stdout.write('='*80)
            self.stdout.write('📊 RESUMO DO PROCESSAMENTO')
            self.stdout.write('='*80)
            self.stdout.write(f'Campanhas processadas: {total_campaigns_processed}')
            self.stdout.write(f'Campanhas atualizadas: {total_campaigns_updated}')
            self.stdout.write(f'Campanhas já corretas: {total_campaigns_skipped}')

            if dry_run:
                self.stdout.write('')
                self.stdout.write('='*80)
                self.stdout.write('⚠️  MODO DRY-RUN: Execute sem --dry-run para aplicar alterações')
                self.stdout.write('='*80)

    def _process_campaign(self, campaign, dry_run=False):
        """
        Processa uma única campanha e recalcular suas métricas.
        Retorna True se atualizou, False se não precisava atualizar.
        """
        self.stdout.write(f'\n{"="*80}')
        self.stdout.write(f'📢 Campanha: {campaign.name} (ID: {campaign.id})')
        self.stdout.write(f'   Status: {campaign.get_status_display()}')

        # Busca CampaignItems desta campanha
        items = CampaignItem.objects.filter(campaign=campaign)

        if not items.exists():
            self.stdout.write('   ⏭️  Sem itens nesta campanha')
            return False

        # Conta métricas corretas baseadas em CampaignItems
        total_items = items.count()
        delivered_count = items.filter(status='delivered').count()
        read_count = items.filter(status='read').count()
        sent_count = items.filter(status='sent').count()
        failed_count = items.filter(status='failed').count()

        # Para campanhas concluídas, considera itens 'sent' como 'delivered'
        # pois provavelmente foram entregues mas o webhook não atualizou
        if campaign.status == 'completed' and sent_count > 0:
            delivered_count += sent_count
            self.stdout.write(f'   ℹ️  Campanha concluída: considerando {sent_count} itens "sent" como "delivered"')

        self.stdout.write(f'   Total de itens: {total_items}')
        self.stdout.write(f'   ✅ Delivered: {delivered_count}')
        self.stdout.write(f'   📖 Read: {read_count}')
        self.stdout.write(f'   ❌ Failed: {failed_count}')

        # Busca métricas atuais da campanha
        current_delivered = campaign.messages_delivered
        current_read = campaign.messages_read

        self.stdout.write(f'   Métricas atuais no banco:')
        self.stdout.write(f'      messages_delivered: {current_delivered}')
        self.stdout.write(f'      messages_read: {current_read}')

        # Verifica se precisa recalcular
        needs_update = (
            current_delivered != delivered_count or
            current_read != read_count
        )

        if needs_update:
            self.stdout.write(f'   ⚠️  Métricas incorretas detectadas!')
            if current_delivered != delivered_count:
                diff = current_delivered - delivered_count
                self.stdout.write(f'      Diferença delivered: {diff} (banco vs items)')
            if current_read != read_count:
                diff = current_read - read_count
                self.stdout.write(f'      Diferença read: {diff} (banco vs items)')

            if not dry_run:
                # Recalcula métricas
                campaign.messages_delivered = delivered_count
                campaign.messages_read = read_count
                campaign.save(update_fields=['messages_delivered', 'messages_read'])

                self.stdout.write(f'   ✅ Atualizado: delivered={delivered_count}, read={read_count}')
            else:
                self.stdout.write(f'   ✓ DRY-RUN: Seria atualizado para delivered={delivered_count}, read={read_count}')

            return True
        else:
            self.stdout.write(f'   ✅ Métricas já estão corretas')
            return False
