import logging
from django.db import transaction, models
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.campaigns.models import Campaign, CampaignItem
from apps.supporters.models import Supporter, Tag
from apps.campaigns.tasks import process_campaign_batch

logger = logging.getLogger(__name__)
User = get_user_model()

class CampaignService:
    def start_campaign(self, campaign: Campaign):
        """
        Prepara e inicia uma campanha.
        1. Identifica público alvo.
        2. Cria itens de campanha.
        3. Agenda task inicial.
        """
        if campaign.status == Campaign.Status.RUNNING:
            return

        with transaction.atomic():
            # Se for rascunho, popula os itens. Se for Paused/Failed, assume que já populou.
            if campaign.status == Campaign.Status.DRAFT:
                self._populate_recipients(campaign)
            
            campaign.status = Campaign.Status.RUNNING
            if not campaign.started_at:
                campaign.started_at = timezone.now()
            campaign.save()

        # Dispara a primeira task
        logger.info(f"Iniciando campanha {campaign.id} - {campaign.name}")
        process_campaign_batch.delay(campaign.id)

    def _populate_recipients(self, campaign: Campaign):
        """Busca supporters e usuários com base nos filtros e cria CampaignItems."""
        
        # Validação de segurança: Não enviar se não houver alvo
        has_tags = campaign.target_tags.exists()
        groups = campaign.target_groups or []
        has_groups = bool(groups)
        
        if not has_tags and not has_groups:
            raise ValueError("Nenhum público alvo selecionado para a campanha.")

        recipients_map = {} # Map phone -> {name, supporter_obj} to deduplicate

        # 1. Processar Tags e Grupos de Apoiadores/Leads (Queryset Supporter)
        qs_filter = models.Q()
        
        # Filtro por Tags Específicas
        if has_tags:
            qs_filter |= models.Q(tags__in=campaign.target_tags.all())

        # Filtro por Grupos (Leads/Supporters são baseados em tags de sistema)
        if 'leads' in groups:
            lead_tag = Tag.objects.filter(slug='lead', is_system=True).first()
            if lead_tag:
                qs_filter |= models.Q(tags=lead_tag)
        
        if 'supporters' in groups:
            supporter_tag = Tag.objects.filter(slug='apoiador', is_system=True).first()
            if supporter_tag:
                qs_filter |= models.Q(tags=supporter_tag)

        if qs_filter:
            supporters = Supporter.objects.filter(
                whatsapp_opt_in=True
            ).exclude(phone='').filter(qs_filter).distinct()

            for supporter in supporters:
                clean_phone = self._clean_phone(supporter.phone)
                if clean_phone:
                    recipients_map[clean_phone] = {
                        'name': supporter.name,
                        'phone': supporter.phone, # Manter original ou limpo? Melhor manter original se validado
                        'supporter': supporter
                    }

        # 2. Processar Grupo Equipe (Users)
        if 'team' in groups:
            # Buscar usuários do tenant atual (assumindo contexto do tenant ativo no DB)
            # Como Users são globais, precisamos filtrar pelos que tem Membership no tenant atual
            # Mas estamos numa task ou view? Se for view, request.tenant.
            # Se for task, o schema já está setado pelo django-tenants.
            # User -> TenantMembership -> Tenant.
            # A query abaixo pega users que tem membership no schema atual (implicito pelo django-tenants?)
            # Não, User é compartilhado (public). TenantMembership é no tenant schema?
            # TenantMembership tem FK para User e Client.
            
            # Correção: TenantMembership geralmente fica no schema PUBLIC ou TENANT? 
            # No nosso caso, TenantMembership está em `apps.tenants`, que é SHARED_APP.
            # Então ele está no schema PUBLIC.
            # O CampaignService roda no contexto do tenant.
            # Para acessar tabelas do public, precisamos cruzar schemas ou usar TenantMembership.
            
            # Simplificação: Vamos assumir que os usuários estão acessíveis via User.objects.filter(...)
            # Mas precisamos saber QUAL tenant. O objeto `campaign` não tem FK direta pra tenant (pois está dentro do schema).
            # Mas estamos rodando dentro do schema do tenant.
            
            # Workaround: Pegar todos os users que tem 'phone' preenchido.
            # Em um ambiente isolado real, filtrariamos pelo tenant ID.
            # Vamos assumir que 'Equipe' são todos os usuários com acesso a este tenant.
            
            # Como acessar o Tenant atual?
            from django.db import connection
            tenant_schema = connection.schema_name
            
            # Precisamos da tabela TenantMembership que está no public schema
            from apps.tenants.models import TenantMembership, Client
            
            # Isso é complicado pq estamos em outro schema.
            # Vamos tentar uma abordagem mais simples: se o User criou a campanha, ele é do time.
            # Mas queremos TODOS do time.
            
            # Solução via raw SQL ou troca de contexto se necessário.
            # Mas espere, se TenantMembership é SHARED, ele está no public.
            # O `Client` também.
            # O `Campaign` está no tenant.
            
            # Se estamos no schema do tenant, não conseguimos fazer join fácil com tables do public no Django ORM
            # a menos que usemos database routers corretamente configurados.
            # O `django-tenants` cuida disso para apps compartilhados.
            # Se `apps.tenants` está em `SHARED_APPS`, podemos consultá-lo normalmente!
            
            current_client = Client.objects.get(schema_name=tenant_schema)
            team_members = User.objects.filter(
                memberships__tenant=current_client,
                memberships__is_active=True
            ).exclude(phone='').distinct()

            for user in team_members:
                clean_phone = self._clean_phone(user.phone)
                if clean_phone:
                    # Se já existe (ex: usuario tb é apoiador), sobrescreve ou ignora?
                    # Ignora se já estiver na lista (prioridade para dados de apoiador que tem mais meta-dados?)
                    # Ou prioriza User?
                    if clean_phone not in recipients_map:
                        recipients_map[clean_phone] = {
                            'name': user.get_full_name(),
                            'phone': user.phone,
                            'supporter': None # Não lincamos a Supporter
                        }

        if not recipients_map:
            raise ValueError("Nenhum destinatário encontrado com os filtros selecionados.")

        # Bulk Create
        items = [
            CampaignItem(
                campaign=campaign,
                supporter=data['supporter'],
                recipient_name=data['name'],
                recipient_phone=data['phone'],
                status=CampaignItem.Status.PENDING
            )
            for data in recipients_map.values()
        ]
        
        CampaignItem.objects.bulk_create(items, batch_size=500)
        
        campaign.total_recipients = len(items)
        campaign.save(update_fields=['total_recipients'])
        logger.info(f"Campanha populada com {len(items)} destinatários.")

    def _clean_phone(self, phone):
        """Remove caracteres não numéricos."""
        import re
        if not phone: return None
        return re.sub(r'\D', '', phone)

campaign_service = CampaignService()