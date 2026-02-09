#!/bin/bash

# ==========================================
# VoxPop - Criar Tenant em Produção
# ==========================================
# Uso no servidor de produção
# docker exec -i voxpop_backend bash -c 'cat > /tmp/create_tenant.py' < create_tenant.py
# docker exec voxpop_backend python /tmp/create_tenant.py

set -e

# Verifica se está rodando dentro do container
if [ ! -f "/app/manage.py" ]; then
    echo "Este script deve ser rodado DENTRO do container backend:"
    echo "  docker exec -it voxpop_backend bash"
    echo "  cd /app && python create_tenant.py"
    exit 1
fi

# Função para criar/atualizar tenant
create_tenant() {
    local TENANT_NAME="$1"
    local OWNER_EMAIL="$2"
    local OWNER_PASSWORD="${3:-VoxPop123!}"
    local DOMAIN="${4}"
    local PHONE="${5:-+5511999999999}"
    local CREATE_WHATSAPP="${6:-false}"
    local WHATSAPP_NAME="${7:-}"
    local WHATSAPP_TOKEN="${8:-}"
    local WHATSAPP_NUMBER="${9:-}"
    local WHATSAPP_LIMIT="${10:-1000}"
    local PLAN_ID="${11:-1}"
    local BASE_URL="${12:-http://localhost:8000}"

    # Gera slug e schema_name
    local SLUG=$(echo "$TENANT_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9-]//g' | sed 's/-$//')
    local SCHEMA_NAME=$(echo "$SLUG" | sed 's/-/_/g')

    echo "Criando tenant: $TENANT_NAME ($SLUG)"

    python << EOF
import django
django.setup()

from django.db import transaction
from django_tenants.utils import schema_context
from apps.tenants.models import Client, Domain, TenantMembership, Plan
from apps.accounts.models import User
from apps.supporters.models import Tag, Segment
from apps.messaging.models import MessageTemplate
from apps.whatsapp.models import WhatsAppSession

# Buscar plano
plan = Plan.objects.get(id=$PLAN_ID)

# Buscar ou criar usuário
try:
    user = User.objects.get(email='$OWNER_EMAIL')
    print(f'Usuário encontrado: {user.email}')
except User.DoesNotExist:
    user = User.objects.create_user(
        email='$OWNER_EMAIL',
        password='$OWNER_PASSWORD',
        first_name='$OWNER_EMAIL',
        is_verified=True
    )
    print(f'Usuário criado: {user.email}')

# Buscar ou criar tenant
try:
    tenant = Client.objects.get(slug='$SLUG')
    print(f'Tenant encontrado: {tenant.name} - ATUALIZANDO')

    # Atualizar
    tenant.name = '$TENANT_NAME'
    tenant.email = '$OWNER_EMAIL'
    tenant.phone = '$PHONE'
    tenant.save()
except Client.DoesNotExist:
    print(f'Criando NOVO tenant: {tenant.name}')

    # Criar schema PostgreSQL
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME}")

    # Criar tenant
    tenant = Client.objects.create(
        schema_name=SCHEMA_NAME,
        name='$TENANT_NAME',
        slug='$SLUG',
        plan=plan,
        email='$OWNER_EMAIL',
        phone='$PHONE',
    )

# Configurar domínio
domain, created = Domain.objects.get_or_create(
    domain='$DOMAIN',
    defaults={'tenant': tenant, 'is_primary': True}
)
if created:
    print(f'Domínio criado: {domain.domain}')
else:
    print(f'Domínio já existe: {domain.domain}')

# Configurar membership
membership, created = TenantMembership.objects.get_or_create(
    user=user,
    tenant=tenant,
    defaults={'role': 'owner'}
)
if created:
    print(f'Membership criada: {user.email} -> {tenant.name}')
else:
    print(f'Membership já existe')

# Inicializar dados se tenant novo
if not tenant.schema_name == 'public':
    with schema_context(tenant.schema_name):
        # Tags de sistema
        tags_data = [
            ('lead', 'Lead', '#3B82F6', 'Contato inicial'),
            ('apoiador', 'Apoiador', '#22C55E', 'Apoiador confirmado'),
            ('blacklist', 'Blacklist', '#EF4444', 'Não contatar'),
        ]
        for slug, name, color, desc in tags_data:
            Tag.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'color': color, 'description': desc, 'is_system': True}
            )
        print('Tags de sistema criadas/verificadas')

        # Segmentos padrão
        segments_data = [
            ('Todos os Contatos', 'Todos os contatos', {}),
            ('Leads', 'Contatos iniciais', {'tags': ['lead']}),
            ('Apoiadores Ativos', 'Apoiadores', {'tags': ['apoiador']}),
        ]
        for name, desc, filters in segments_data:
            Segment.objects.get_or_create(
                name=name,
                defaults={'description': desc, 'filters': filters, 'created_by': user}
            )
        print('Segmentos criados/verificados')

        # Template padrão
        MessageTemplate.objects.get_or_create(
            name='Boas-vindas',
            defaults={
                'description': 'Mensagem de boas-vindas',
                'message_type': 'text',
                'content': 'Olá {{name}}! Bem-vindo!',
                'variables': ['name'],
                'created_by': user
            }
        )
        print('Template criado/verificado')

# WhatsApp (se solicitado)
if '$CREATE_WHATSAPP' == 'true':
    with schema_context(tenant.schema_name):
        session, created = WhatsAppSession.objects.update_or_create(
            instance_name='$WHATSAPP_NAME',
            defaults={
                'name': '$WHATSAPP_NAME',
                'status': 'connected',
                'phone_number': '$WHATSAPP_NUMBER',
                'access_token': '$WHATSAPP_TOKEN',
                'webhook_url': f'{BASE_URL}/api/v1/whatsapp/webhook/{$WHATSAPP_NAME}/',
                'daily_message_limit': $WHATSAPP_LIMIT,
                'is_active': True
            }
        )
        if created:
            print(f'Sessão WhatsApp CRIADA: {session.name} (ID: {session.id})')
        else:
            print(f'Sessão WhatsApp ATUALIZADA: {session.name} (ID: {session.id})')

print(f'\n=== TENANT PRONTO ===')
print(f'ID: {tenant.id}')
print(f'Nome: {tenant.name}')
print(f'Slug: {tenant.slug}')
print(f'Schema: {tenant.schema_name}')
print(f'Domínio: {Domain.objects.filter(tenant=tenant, is_primary=True).first().domain}')
print(f'\nAcesso:')
print(f'  Frontend:  http://{Domain.objects.filter(tenant=tenant, is_primary=True).first().domain}:5173')
print(f'  Backend:   http://{Domain.objects.filter(tenant=tenant, is_primary=True).first().domain}:8000/api/v1')
EOF
}

# Executar com argumentos
if [ $# -lt 2 ]; then
    echo "Uso: $0 <nome> <email> [senha] [domínio] [telefone] [whatsapp] [nome_wa] [token_wa] [numero_wa] [limite] [plano_id] [base_url]"
    echo ""
    echo "Exemplo:"
    echo "  $0 'Campanha João' 'joao@email.com'"
    echo "  $0 'Campanha Maria' 'maria@email.com' 'Senha123' 'maria.voxpop.com' '+5511999999999' 'true' 'Principal' 'TOKEN123' '+55119999999988' 2000 1 'https://voxpop.tratto.solutions'"
    exit 1
fi

create_tenant "$@"
