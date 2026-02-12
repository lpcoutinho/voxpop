"""
Management command para criar um novo tenant completo com integração WhatsApp.

Este comando cria:
1. Tenant (Client) com seu schema PostgreSQL
2. Domínio para acesso
3. Usuário admin (owner) do tenant
4. Sessão WhatsApp na Evolution API
5. Tags do sistema para o tenant

Uso:
    python manage.py create_tenant_full          # Interativo
    python manage.py create_tenant_full --help   # Ver opções
"""
import sys
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from django_tenants.utils import schema_context

from apps.accounts.models import User
from apps.tenants.models import Client, Domain, Plan, TenantMembership
from apps.whatsapp.models import WhatsAppSession
from apps.whatsapp.services.whatsapp_service import WhatsAppService
from core.exceptions import EvolutionAPIError


class Command(BaseCommand):
    help = 'Cria um novo tenant completo com integração WhatsApp (tenant, domínio, sessão WhatsApp, tags do sistema)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            help='Nome da organização/político',
        )
        parser.add_argument(
            '--slug',
            type=str,
            help='Slug único do tenant (usado no schema_name)',
        )
        parser.add_argument(
            '--domain',
            type=str,
            help='Domínio do tenant (ex: joao.localhost ou joao.voxpop.com.br)',
        )
        parser.add_argument(
            '--plan',
            type=str,
            default='basic',
            help='Plano de assinatura (default: basic)',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='E-mail de contato',
        )
        parser.add_argument(
            '--phone',
            type=str,
            help='Telefone de contato',
        )
        parser.add_argument(
            '--document',
            type=str,
            help='CNPJ (opcional)',
        )
        parser.add_argument(
            '--session-name',
            type=str,
            help='Nome da sessão WhatsApp (default: mesmo do slug)',
        )
        parser.add_argument(
            '--evolution-token',
            type=str,
            help='Token customizado para a instância na Evolution API (opcional)',
        )
        parser.add_argument(
            '--existing-instance',
            action='store_true',
            help='Registra instância já existente na Evolution API (não cria nova)',
        )
        parser.add_argument(
            '--no-whatsapp',
            action='store_true',
            help='Não criar instância WhatsApp',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Senha do usuário admin do tenant',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a execução sem salvar alterações',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        self.stdout.write('='*80)
        self.stdout.write('CRIAR TENANT COMPLETO - VoxPop')
        self.stdout.write('='*80)
        self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  MODO DRY-RUN - Nenhuma alteração será salva'))
            self.stdout.write('')

        # Coleta dados (se não informados via argumentos)
        data = self._collect_data(options)

        self.stdout.write('')
        self.stdout.write('='*80)
        self.stdout.write('Resumo da Criação:')
        self.stdout.write('='*80)
        self._print_summary(data)

        if not dry_run:
            # Confirmação
            self.stdout.write('')
            confirm = input('Confirma a criação do tenant? [y/N]: ')
            if confirm.lower() != 'y':
                self.stdout.write(self.style.WARNING('❌ Operação cancelada'))
                return

        # Executa a criação
        try:
            result = self._create_tenant(data, dry_run)
            self._print_result(result, data)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao criar tenant: {str(e)}'))
            raise

    def _collect_data(self, options):
        """Coleta os dados do tenant (interativo se necessário)."""
        data = {}

        # Nome
        if options.get('name'):
            data['name'] = options['name']
        else:
            data['name'] = input('Nome da organização/político: ').strip()

        # Slug
        if options.get('slug'):
            data['slug'] = options['slug']
        else:
            default_slug = data['name'].lower().replace(' ', '-')[:50]
            slug_input = input(f'Slug (pressione Enter para "{default_slug}"): ').strip()
            data['slug'] = slug_input or default_slug

        # Valida slug
        if not data['slug'].isalnum() and '-' not in data['slug']:
            self.stdout.write(self.style.ERROR('❌ Slug deve conter apenas letras, números e hífens'))
            sys.exit(1)

        # Domínio
        if options.get('domain'):
            data['domain'] = options['domain']
        else:
            default_domain = f"{data['slug']}.localhost"
            domain_input = input(f'Domínio (pressione Enter para "{default_domain}"): ').strip()
            data['domain'] = domain_input or default_domain

        # Plano
        plan_slug = options.get('plan', 'basic')
        try:
            plan = Plan.objects.get(slug=plan_slug)
            data['plan'] = plan
            self.stdout.write(f'✓ Plano: {plan.name}')
        except Plan.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Plano "{plan_slug}" não encontrado'))
            sys.exit(1)

        # Email
        data['email'] = options.get('email', '') or input('E-mail (opcional): ').strip() or ''

        # Telefone
        data['phone'] = options.get('phone', '') or input('Telefone (opcional): ').strip() or ''

        # Documento (CNPJ)
        data['document'] = options.get('document', '') or input('CNPJ (opcional): ').strip() or ''

        # Senha do admin
        if options.get('password'):
            data['password'] = options['password']
        else:
            import getpass
            while True:
                pwd = getpass.getpass('Senha do admin: ')
                pwd2 = getpass.getpass('Confirme a senha: ')
                if pwd == pwd2:
                    data['password'] = pwd
                    break
                self.stdout.write(self.style.ERROR('❌ Senhas não conferem, tente novamente'))

        # WhatsApp
        data['no_whatsapp'] = options.get('no_whatsapp', False)
        data['existing_instance'] = options.get('existing_instance', False)

        if not data['no_whatsapp']:
            if options.get('session_name'):
                data['session_name'] = options['session_name']
            else:
                data['session_name'] = data['slug']

            # Token da Evolution API (opcional) - OBRIGATÓRIO para instância existente
            if data['existing_instance']:
                token_input = input('Token da Evolution API da instância existente (OBRIGATÓRIO): ').strip()
                if not token_input:
                    self.stdout.write(self.style.ERROR('❌ Token é obrigatório para registrar instância existente'))
                    sys.exit(1)
                data['evolution_token'] = token_input
            else:
                data['evolution_token'] = options.get('evolution_token', '') or input('Token da Evolution API (opcional, Enter para gerar automaticamente): ').strip() or ''

        return data

    def _print_summary(self, data):
        """Imprime resumo dos dados."""
        self.stdout.write(f'Nome: {data["name"]}')
        self.stdout.write(f'Slug/Schema: {data["slug"]}')
        self.stdout.write(f'Domínio: {data["domain"]}')
        self.stdout.write(f'Plano: {data["plan"].name}')
        if data.get('email'):
            self.stdout.write(f'E-mail: {data["email"]}')
        if data.get('phone'):
            self.stdout.write(f'Telefone: {data["phone"]}')
        if data.get('document'):
            self.stdout.write(f'CNPJ: {data["document"]}')
        self.stdout.write(f'Admin: {data["email"]}')
        self.stdout.write(f'Senha: {"*" * len(data.get("password", ""))}')
        if not data.get('no_whatsapp'):
            self.stdout.write(f'Sessão WhatsApp: {data["session_name"]}')
            if data.get('existing_instance'):
                self.stdout.write(f'   (Instância existente - apenas registro no banco)')
            if data.get('evolution_token'):
                self.stdout.write(f'Token Evolution: {data["evolution_token"][:10]}...***')

    def _print_result(self, result, data):
        """Imprime o resultado da criação."""
        self.stdout.write('')
        self.stdout.write('='*80)
        self.stdout.write(self.style.SUCCESS('✅ TENANT CRIADO COM SUCESSO!'))
        self.stdout.write('='*80)
        self.stdout.write('')

        self.stdout.write('📋 Dados do Tenant:')
        self.stdout.write(f'   Nome: {result["client"].name}')
        self.stdout.write(f'   Schema: {result["client"].schema_name}')
        self.stdout.write(f'   Domínio: {result["domain"].domain}')
        self.stdout.write(f'   Plano: {result["client"].plan.name}')
        self.stdout.write('')

        if result.get('user'):
            self.stdout.write('👤 Usuário Admin:')
            self.stdout.write(f'   E-mail: {result["user"].email}')
            self.stdout.write(f'   Nome: {result["user"].get_full_name()}')
            self.stdout.write('')

        if result.get('session'):
            session = result['session']
            self.stdout.write('📱 Sessão WhatsApp:')
            self.stdout.write(f'   Nome: {session.name}')
            self.stdout.write(f'   Instância: {session.instance_name}')
            self.stdout.write(f'   Status: {session.get_status_display()}')
            if session.access_token:
                self.stdout.write(f'   Token: {session.access_token[:10]}...***')
            self.stdout.write('')

            # URL DO WEBHOOK
            webhook_url = self._get_webhook_url(session.instance_name)
            self.stdout.write('='*80)
            self.stdout.write(self.style.SUCCESS('🔗 URL DO WEBHOOK - CONFIGURE NA EVOLUTION API'))
            self.stdout.write('='*80)
            self.stdout.write('')
            self.stdout.write(f'{webhook_url}')
            self.stdout.write('')
            self.stdout.write('='*80)
            self.stdout.write('')
            self.stdout.write('Para configurar na Evolution API:')
            self.stdout.write(f'   1. Acesse a instância: {session.instance_name}')
            self.stdout.write(f'   2. Configure o webhook com a URL acima')
            self.stdout.write(f'   3. Gere o QR Code e conecte o WhatsApp')
            self.stdout.write('')

        if result.get('tags_created'):
            self.stdout.write(f'🏷️  {result["tags_created"]} tags do sistema criadas')

    def _get_webhook_url(self, instance_name: str) -> str:
        """Retorna a URL do webhook para a instância."""
        base_url = settings.BASE_URL.rstrip('/')
        return f'{base_url}/api/whatsapp/webhook/evolution/{instance_name}/'

    @transaction.atomic
    def _create_tenant(self, data, dry_run=False):
        """Cria o tenant e todos os recursos associados."""
        result = {}

        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  DRY-RUN: Não criando nada'))
            return result

        # 1. Cria o Client (Tenant)
        self.stdout.write('')
        self.stdout.write('📦 Criando tenant...')

        client = Client.objects.create(
            name=data['name'],
            slug=data['slug'],
            schema_name=data['slug'],  # schema_name = slug
            plan=data['plan'],
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            document=data.get('document', ''),
            is_active=True,
        )
        result['client'] = client
        self.stdout.write(f'   ✅ Tenant criado (schema: {client.schema_name})')

        # 2. Cria o Domínio
        self.stdout.write('🌐 Criando domínio...')

        is_primary = True
        domain = Domain.objects.create(
            domain=data['domain'],
            tenant=client,
            is_primary=is_primary,
        )
        result['domain'] = domain
        self.stdout.write(f'   ✅ Domínio criado: {domain.domain}')

        # 3. Cria a instância WhatsApp (se solicitado)
        if not data.get('no_whatsapp'):
            whatsapp_service = WhatsAppService()
            webhook_url = self._get_webhook_url(data['session_name'])
            evolution_token = data.get('evolution_token', '')
            is_existing = data.get('existing_instance', False)

            if is_existing:
                # Apenas registra instância existente no banco
                self.stdout.write('📱 Registrando instância WhatsApp existente...')

                if not evolution_token:
                    self.stdout.write(self.style.ERROR('   ❌ Token é obrigatório para registrar instância existente'))
                    raise ValueError('Token obrigatório para instância existente')

                with schema_context(client.schema_name):
                    session = WhatsAppSession.objects.create(
                        name=f'{data["name"]} - WhatsApp',
                        instance_name=data['session_name'],
                        access_token=evolution_token,
                        webhook_url=webhook_url,
                        status='connected',
                        daily_message_limit=data['plan'].max_messages_month // 30,
                    )
                result['session'] = session
                self.stdout.write(f'   ✅ Sessão registrada no banco (status: conectado)')
                self.stdout.write(f'   🔑 Token: {evolution_token[:10]}...***')
            else:
                # Cria nova instância na Evolution API
                self.stdout.write('📱 Criando instância WhatsApp...')

                try:
                    instance_data = whatsapp_service.create_instance_sync(
                        instance_name=data['session_name'],
                        webhook_url=webhook_url,
                        token=evolution_token,
                    )
                    self.stdout.write(f'   ✅ Instância criada na Evolution API')

                    # Se foi fornecido token customizado, usa ele; senão usa o retornado
                    if evolution_token:
                        access_token = evolution_token
                    else:
                        access_token = instance_data.get('instance', {}).get('token', {}).get('token', '')

                except EvolutionAPIError as e:
                    self.stdout.write(self.style.WARNING(f'   ⚠️  Erro ao criar instância Evolution: {e}'))
                    instance_data = {}
                    access_token = evolution_token  # Usa token fornecido mesmo se der erro na API

                # Cria sessão no banco
                with schema_context(client.schema_name):
                    session = WhatsAppSession.objects.create(
                        name=f'{data["name"]} - WhatsApp',
                        instance_name=data['session_name'],
                        access_token=access_token,
                        webhook_url=webhook_url,
                        status='disconnected',
                        daily_message_limit=data['plan'].max_messages_month // 30,  # limite diário aprox
                    )
                result['session'] = session
                self.stdout.write(f'   ✅ Sessão criada no banco')

                if access_token:
                    self.stdout.write(f'   🔑 Token: {access_token[:10]}...***')

        # 4. Cria usuário admin (owner) do tenant
        self.stdout.write('👤 Criando usuário admin...')

        user, created = User.objects.get_or_create(
            email=data['email'],
            defaults={
                'first_name': data['name'].split()[0] if data['name'] else '',
                'last_name': ' '.join(data['name'].split()[1:]) if len(data['name'].split()) > 1 else '',
                'phone': data.get('phone', ''),
                'is_active': True,
                'is_verified': True,
            }
        )
        if created:
            user.set_password(data['password'])
            user.save()
            self.stdout.write(f'   ✅ Usuário criado: {user.email}')
        else:
            self.stdout.write(f'   ℹ️  Usuário já existe: {user.email}')

        membership, m_created = TenantMembership.objects.get_or_create(
            user=user,
            tenant=client,
            defaults={'role': TenantMembership.Role.OWNER}
        )
        if m_created:
            self.stdout.write(f'   ✅ Membership criada (role: owner)')
        result['user'] = user

        # 5. Cria tags do sistema no schema do tenant
        self.stdout.write('🏷️  Criando tags do sistema...')

        with schema_context(client.schema_name):
            from apps.supporters.models import Tag

            tags_created = Tag.create_system_tags()
            result['tags_created'] = len(tags_created)
            self.stdout.write(f'   ✅ {len(tags_created)} tags criadas')

        return result
