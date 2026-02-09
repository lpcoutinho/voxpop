#!/bin/bash

# ==========================================
# VoxPop - Script para Criar Novo Tenant (via Banco de Dados)
# ==========================================
# Uso: ./create-tenant.sh <nome> <email> [senha] [domínio] [telefone] [criar_whatsapp] [nome_whatsapp] [token_whatsapp> [numero_whatsapp] [limite_mensagens]
# Exemplo: ./create-tenant.sh "Campanha João" "joao@exemplo.com" "Senha123" "joao.localhost" "+5511999999999" "true" "Principal" "token123" "+55119999999988" 1000

set -e

# Configurações
DB_CONTAINER="${DB_CONTAINER:-voxpop_db}"
DB_NAME="${DB_NAME:-voxpop_db}"
DB_USER="${DB_USER:-voxpop}"
BACKEND_CONTAINER="${BACKEND_CONTAINER:-voxpop_backend}"
DEFAULT_PLAN_ID="${DEFAULT_PLAN_ID:-1}"
DEFAULT_PASSWORD="${DEFAULT_PASSWORD:-VoxPop123!}"
BASE_URL="${BASE_URL:-http://localhost:8000}"

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Função de ajuda
usage() {
    echo "Uso: $0 <nome> <email> [senha] [domínio] [telefone] [criar_whatsapp] [nome_whatsapp] [token_whatsapp] [numero_whatsapp] [limite_mensagens]"
    echo ""
    echo "Argumentos:"
    echo "  nome              Nome da organização (obrigatório)"
    echo "  email             E-mail do proprietário (obrigatório)"
    echo "  senha             Senha do usuário (opcional, padrão: VoxPop123!)"
    echo "  domínio           Subdomínio desejado (opcional, padrão: baseado no nome)"
    echo "  telefone          Telefone de contato do usuário (opcional)"
    echo "  criar_whatsapp   Criar sessão WhatsApp (opcional, true/false, padrão: false)"
    echo "  nome_whatsapp     Nome da sessão WhatsApp (obrigatório se criar_whatsapp=true)"
    echo "  token_whatsapp    Token da Evolution API (obrigatório se criar_whatsapp=true)"
    echo "  numero_whatsapp   Número conectado ao WhatsApp (obrigatório se criar_whatsapp=true)"
    echo "  limite_mensagens  Limite diário de mensagens (opcional, padrão: 1000)"
    echo ""
    echo "Variáveis de ambiente:"
    echo "  DB_CONTAINER        Container do banco (padrão: voxpop_db)"
    echo "  BACKEND_CONTAINER   Container do backend (padrão: voxpop_backend)"
    echo "  DB_NAME             Nome do banco (padrão: voxpop_db)"
    echo "  DB_USER             Usuário do banco (padrão: voxpop)"
    echo "  DEFAULT_PLAN_ID     ID do plano (padrão: 1)"
    echo "  DEFAULT_PASSWORD    Senha padrão (padrão: VoxPop123!)"
    echo "  BASE_URL            URL base do backend (padrão: http://localhost:8000)"
    echo ""
    echo "Exemplos:"
    echo "  $0 'Campanha João' 'joao@exemplo.com'"
    echo "  $0 'Campanha Maria' 'maria@exemplo.com' 'SenhaForte123!' 'maria.localhost' '+5511888888888'"
    echo "  $0 'Campanha Pedro' 'pedro@exemplo.com' 'Senha123' 'pedro.localhost' '+5511877777777' 'true' 'Principal' 'abc123token' '+55119999999988' 2000"
    exit 1
}

# Verifica argumentos
if [ -z "$1" ] || [ -z "$2" ]; then
    usage
fi

# Parâmetros
TENANT_NAME="$1"
OWNER_EMAIL="$2"
OWNER_PASSWORD="${3:-$DEFAULT_PASSWORD}"
DOMAIN="${4:-$(echo "$1" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9-]//g' | sed 's/-$//').localhost}"
PHONE="${5:-+5511999999999}"
CREATE_WHATSAPP="${6:-false}"
WHATSAPP_NAME="${7:-}"
WHATSAPP_TOKEN="${8:-}"
WHATSAPP_NUMBER="${9:-}"
WHATSAPP_LIMIT="${10:-1000}"

# Validações para WhatsApp
if [ "$CREATE_WHATSAPP" = "true" ]; then
    if [ -z "$WHATSAPP_NAME" ] || [ -z "$WHATSAPP_TOKEN" ] || [ -z "$WHATSAPP_NUMBER" ]; then
        echo -e "${RED}✗ Erro: Para criar WhatsApp, informe nome, token e número${NC}"
        echo "  Uso: $0 '$TENANT_NAME' '$OWNER_EMAIL' '$OWNER_PASSWORD' '$DOMAIN' '$PHONE' 'true' 'Nome Sessão' 'TokenAPI' '+55119999999988' [limite]"
        exit 1
    fi
fi

# Gera slug e schema_name
SLUG=$(echo "$1" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9-]//g' | sed 's/-$//')
SCHEMA_NAME=$(echo "$SLUG" | sed 's/-/_/g')

# Nome e sobrenome do usuário (baseado no email)
FIRST_NAME=$(echo "$OWNER_EMAIL" | cut -d'@' -f1 | sed 's/[^a-zA-Z]//g' | sed 's/^\(.\)/\U\1/')
LAST_NAME="Admin"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}VoxPop - Criar Novo Tenant${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Nome:${NC} $TENANT_NAME"
echo -e "${GREEN}Slug:${NC} $SLUG"
echo -e "${GREEN}Schema:${NC} $SCHEMA_NAME"
echo -e "${GREEN}E-mail:${NC} $OWNER_EMAIL"
echo -e "${GREEN}Senha:${NC} $OWNER_PASSWORD"
echo -e "${GREEN}Domínio:${NC} $DOMAIN"
echo -e "${GREEN}Telefone:${NC} $PHONE"
echo -e "${GREEN}Criar WhatsApp:${NC} $CREATE_WHATSAPP"
if [ "$CREATE_WHATSAPP" = "true" ]; then
    echo -e "${CYAN}  └─ Nome Sessão:${NC} $WHATSAPP_NAME"
    echo -e "${CYAN}  └─ Token:${NC} ${WHATSAPP_TOKEN:0:20}..."
    echo -e "${CYAN}  └─ Número:${NC} $WHATSAPP_NUMBER"
    echo -e "${CYAN}  └─ Limite Msg:${NC} $WHATSAPP_LIMIT/dia"
fi
echo ""

# Função para executar SQL no banco
exec_sql() {
    docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c "$1"
}

# Função para executar SQL no schema do tenant
exec_tenant_sql() {
    docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SET search_path TO $SCHEMA_NAME; $1"
}

# Função para verificar se registro existe
record_exists() {
    local count=$(exec_sql "SELECT COUNT(*) FROM $1 WHERE $2;" 2>/dev/null | tr -d ' ')
    [ -n "$count" ] && [ "$count" != "0" ]
}

# Passo 1: Verificar se plano existe
echo -e "${YELLOW}[1/9]${NC} Verificando plano..."
PLAN_EXISTS=$(exec_sql "SELECT COUNT(*) FROM tenants_plan WHERE id = $DEFAULT_PLAN_ID;" | tr -d ' ')
if [ "$PLAN_EXISTS" = "0" ]; then
    echo -e "${RED}✗ Plano ID $DEFAULT_PLAN_ID não encontrado${NC}"
    echo "Planos disponíveis:"
    exec_sql "SELECT id, name FROM tenants_plan ORDER BY id;"
    exit 1
fi
echo -e "${GREEN}✓ Plano encontrado${NC}"

# Passo 2: Verificar se usuário já existe
echo -e "${YELLOW}[2/9]${NC} Verificando se usuário já existe..."
if record_exists "accounts_user" "email = '$OWNER_EMAIL'"; then
    echo -e "${YELLOW}⚠ Usuário '$OWNER_EMAIL' já existe, usando existente${NC}"
    USER_ID=$(exec_sql "SELECT id FROM accounts_user WHERE email = '$OWNER_EMAIL';" | tr -d ' ')
else
    # Criar usuário
    echo -e "${YELLOW}[3/9]${NC} Criando usuário..."

    # Hash da senha (usando Python no container Django)
    PASSWORD_HASH=$(docker exec "$BACKEND_CONTAINER" python -c "
import django
django.setup()
from django.contrib.auth.hashers import make_password
print(make_password('$OWNER_PASSWORD'))
" 2>/dev/null)

    # Inserir usuário
    exec_sql "
        INSERT INTO accounts_user (
            password, is_superuser, is_staff, is_active, email,
            first_name, last_name, phone, is_verified, force_password_change,
            date_joined, last_login
        ) VALUES (
            '$PASSWORD_HASH', false, false, true, '$OWNER_EMAIL',
            '$FIRST_NAME', '$LAST_NAME', '$PHONE', true, false,
            NOW(), NOW()
        ) RETURNING id;
    " > /tmp/user_id.txt 2>&1

    USER_ID=$(cat /tmp/user_id.txt | head -1 | tr -d ' ')
    rm -f /tmp/user_id.txt
    echo -e "${GREEN}✓ Usuário criado (ID: $USER_ID)${NC}"
fi

# Passo 3: Verificar se tenant já existe
echo -e "${YELLOW}[4/9]${NC} Verificando se tenant já existe..."
TENANT_EXISTS=false
if record_exists "tenants_client" "slug = '$SLUG'"; then
    echo -e "${YELLOW}⚠ Tenant '$SLUG' já existe, atualizando...${NC}"
    TENANT_EXISTS=true
    TENANT_ID=$(exec_sql "SELECT id FROM tenants_client WHERE slug = '$SLUG';" | tr -d ' ')
fi

# Passo 4: Criar ou atualizar tenant
if [ "$TENANT_EXISTS" = false ]; then
    echo -e "${YELLOW}[5/9]${NC} Criando tenant..."

    # Inserir tenant
    exec_sql "
        INSERT INTO tenants_client (
            schema_name, name, slug, document, plan_id,
            is_active, settings, email, phone, created_at, updated_at
        ) VALUES (
            '$SCHEMA_NAME', '$TENANT_NAME', '$SLUG', '', $DEFAULT_PLAN_ID,
            true, '{}', '$OWNER_EMAIL', '$PHONE', NOW(), NOW()
        ) RETURNING id;
    " > /tmp/tenant_id.txt 2>&1

    TENANT_ID=$(cat /tmp/tenant_id.txt | head -1 | tr -d ' ')
    rm -f /tmp/tenant_id.txt

    if [ -z "$TENANT_ID" ]; then
        echo -e "${RED}✗ Erro ao criar tenant${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Tenant criado (ID: $TENANT_ID)${NC}"
else
    echo -e "${YELLOW}[5/9]${NC} Atualizando tenant..."

    # Atualizar tenant
    exec_sql "
        UPDATE tenants_client
        SET name = '$TENANT_NAME',
            email = '$OWNER_EMAIL',
            phone = '$PHONE',
            updated_at = NOW()
        WHERE slug = '$SLUG';
    " >/dev/null 2>&1

    echo -e "${GREEN}✓ Tenant atualizado (ID: $TENANT_ID)${NC}"
fi

# Passo 5: Criar schema PostgreSQL e rodar migrações (só se tenant novo)
if [ "$TENANT_EXISTS" = false ]; then
    echo -e "${YELLOW}[6/9]${NC} Criando schema PostgreSQL e rodando migrações..."

    # Criar schema
    docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "CREATE SCHEMA $SCHEMA_NAME;" >/dev/null 2>&1

    # Rodar migrações no schema
    docker exec "$BACKEND_CONTAINER" python manage.py migrate_schemas --schema="$SCHEMA_NAME" >/dev/null 2>&1
    echo -e "${GREEN}✓ Schema e migrações criados${NC}"
else
    echo -e "${YELLOW}[6/9]${NC} ${YELLOW}⊘ Schema já existe, pulando...${NC}"
fi

# Passo 6: Criar/atualizar domínio
echo -e "${YELLOW}[7/9]${NC} Configurando domínio..."
DOMAIN_EXISTS=$(exec_sql "SELECT COUNT(*) FROM tenants_domain WHERE domain = '$DOMAIN';" | tr -d ' ')
if [ "$DOMAIN_EXISTS" = "0" ]; then
    exec_sql "
        INSERT INTO tenants_domain (domain, tenant_id, is_primary)
        VALUES ('$DOMAIN', $TENANT_ID, true);
    " >/dev/null 2>&1
    echo -e "${GREEN}✓ Domínio criado${NC}"
else
    echo -e "${YELLOW}⊘ Domínio já existe${NC}"
fi

# Passo 7: Criar membership (se não existir)
echo -e "${YELLOW}[8/9]${NC} Configurando associação usuário-tenant..."
MEMBERSHIP_EXISTS=$(exec_sql "SELECT COUNT(*) FROM tenants_tenantmembership WHERE user_id = $USER_ID AND tenant_id = $TENANT_ID;" | tr -d ' ')
if [ "$MEMBERSHIP_EXISTS" = "0" ]; then
    exec_sql "
        INSERT INTO tenants_tenantmembership (
            user_id, tenant_id, role, is_active, created_at, updated_at
        ) VALUES (
            $USER_ID, $TENANT_ID, 'owner', true, NOW(), NOW()
        );
    " >/dev/null 2>&1
    echo -e "${GREEN}✓ Associação criada${NC}"
else
    echo -e "${YELLOW}⊘ Associação já existe${NC}"
fi

# Passo 8: Inicializar dados do tenant (via Django ORM) - só se tenant novo
if [ "$TENANT_EXISTS" = false ]; then
    echo -e "${YELLOW}[9/10]${NC} Inicializando dados do tenant..."
    docker exec "$BACKEND_CONTAINER" python manage.py shell << EOF
from django_tenants.utils import schema_context
from apps.tenants.models import Client
from apps.accounts.models import User

tenant = Client.objects.get(id=$TENANT_ID)
user = User.objects.get(id=$USER_ID)

with schema_context(tenant.schema_name):
    from apps.supporters.models import Tag, Segment
    from apps.messaging.models import MessageTemplate

    # Criar tags de sistema
    tags_data = [
        ('lead', 'Lead', '#3B82F6', 'Contato inicial - ainda não é apoiador'),
        ('apoiador', 'Apoiador', '#22C55E', 'Contato engajado - apoiador confirmado'),
        ('blacklist', 'Blacklist', '#EF4444', 'Não contatar - excluído de campanhas'),
    ]
    for slug, name, color, description in tags_data:
        Tag.objects.get_or_create(
            slug=slug,
            defaults={'name': name, 'color': color, 'description': description, 'is_system': True}
        )

    # Criar segmentos padrão
    segments_data = [
        ('Todos os Contatos', 'Todos os contatos cadastrados', {}),
        ('Leads', 'Contatos iniciais - ainda não são apoiadores', {'tags': ['lead']}),
        ('Apoiadores Ativos', 'Contatos engajados - apoiadores confirmados', {'tags': ['apoiador']}),
    ]
    for name, description, filters in segments_data:
        Segment.objects.get_or_create(
            name=name,
            defaults={'description': description, 'filters': filters, 'created_by': user}
        )

    # Criar template padrão
    MessageTemplate.objects.get_or_create(
        name='Boas-vindas',
        defaults={
            'description': 'Mensagem de boas-vindas para novos contatos',
            'message_type': 'text',
            'content': 'Olá {{name}}! Seja bem-vindo(a) à nossa campanha. Estamos felizes em ter você conosco!',
            'variables': ['name'],
            'created_by': user
        }
    )

    print('OK')
EOF

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Dados inicializados${NC}"
    else
        echo -e "${YELLOW}⚠ Aviso: Não foi possível inicializar os dados padrão${NC}"
    fi
else
    echo -e "${YELLOW}[9/10]${NC} ${YELLOW}⊘ Tenant já existe, pulando inicialização...${NC}"
fi

# Passo 9: Criar ou atualizar sessão WhatsApp (se solicitado)
WHATSAPP_SESSION_ID=""
if [ "$CREATE_WHATSAPP" = "true" ]; then
    echo -e "${YELLOW}[10/10]${NC} Configurando sessão WhatsApp..."

    # Webhook URL
    WEBHOOK_URL="${BASE_URL}/api/v1/whatsapp/webhook/${WHATSAPP_NAME}/"

    # Criar ou atualizar sessão usando Django ORM
    WHATSAPP_RESULT=$(docker exec "$BACKEND_CONTAINER" python manage.py shell << EOF
from django_tenants.utils import schema_context
from apps.tenants.models import Client
from apps.whatsapp.models import WhatsAppSession

tenant = Client.objects.get(id=$TENANT_ID)

with schema_context(tenant.schema_name):
    # Verificar se sessão já existe
    existing = WhatsAppSession.objects.filter(instance_name='$WHATSAPP_NAME').first()

    if existing:
        # Atualizar sessão existente
        existing.name = '$WHATSAPP_NAME'
        existing.instance_name = '$WHATSAPP_NAME'
        existing.status = 'connected'
        existing.phone_number = '$WHATSAPP_NUMBER'
        existing.access_token = '$WHATSAPP_TOKEN'
        existing.webhook_url = '$WEBHOOK_URL'
        existing.daily_message_limit = $WHATSAPP_LIMIT
        existing.is_active = True
        existing.save()
        print(f'UPDATE:{existing.id}')
    else:
        # Criar nova sessão
        session = WhatsAppSession.objects.create(
            name='$WHATSAPP_NAME',
            instance_name='$WHATSAPP_NAME',
            status='connected',
            phone_number='$WHATSAPP_NUMBER',
            access_token='$WHATSAPP_TOKEN',
            webhook_url='$WEBHOOK_URL',
            daily_message_limit=$WHATSAPP_LIMIT
        )
        print(f'CREATE:{session.id}')
EOF
)

    WHATSAPP_ACTION=$(echo "$WHATSAPP_RESULT" | tail -1 | grep -oP '(UPDATE|CREATE)' || echo "")
    WHATSAPP_SESSION_ID=$(echo "$WHATSAPP_RESULT" | tail -1 | grep -oP '\d+' || echo "")

    if [ -n "$WHATSAPP_SESSION_ID" ]; then
        if [ "$WHATSAPP_ACTION" = "UPDATE" ]; then
            echo -e "${GREEN}✓ Sessão WhatsApp atualizada (ID: $WHATSAPP_SESSION_ID)${NC}"
        else
            echo -e "${GREEN}✓ Sessão WhatsApp criada (ID: $WHATSAPP_SESSION_ID)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Aviso: Não foi possível configurar a sessão WhatsApp${NC}"
    fi
else
    echo -e "${YELLOW}[10/10]${NC} ${YELLOW}⊘ WhatsApp não solicitado, pulando...${NC}"
fi

# Resultado
echo ""
echo -e "${BLUE}========================================${NC}"
if [ "$TENANT_EXISTS" = true ]; then
    echo -e "${GREEN}✓ Tenant atualizado com sucesso!${NC}"
else
    echo -e "${GREEN}✓ Tenant criado com sucesso!${NC}"
fi
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${BLUE}Dados do Tenant:${NC}"
echo -e "  ID:       ${GREEN}$TENANT_ID${NC}"
echo -e "  Nome:     ${GREEN}$TENANT_NAME${NC}"
echo -e "  Slug:     ${GREEN}$SLUG${NC}"
echo -e "  Schema:   ${GREEN}$SCHEMA_NAME${NC}"
echo -e "  Domínio:  ${GREEN}$DOMAIN${NC}"
echo ""
echo -e "${BLUE}Dados do Usuário:${NC}"
echo -e "  ID:       ${GREEN}$USER_ID${NC}"
echo -e "  E-mail:   ${GREEN}$OWNER_EMAIL${NC}"
if [ "$TENANT_EXISTS" = false ]; then
    echo -e "  Senha:    ${GREEN}$OWNER_PASSWORD${NC}"
fi
echo ""

if [ "$CREATE_WHATSAPP" = "true" ] && [ -n "$WHATSAPP_SESSION_ID" ]; then
    echo -e "${CYAN}Sessão WhatsApp:${NC}"
    echo -e "  ID:           ${CYAN}$WHATSAPP_SESSION_ID${NC}"
    echo -e "  Nome:         ${CYAN}$WHATSAPP_NAME${NC}"
    echo -e "  Instance:     ${CYAN}$WHATSAPP_NAME${NC}"
    echo -e "  Token:        ${CYAN}${WHATSAPP_TOKEN}${NC}"
    echo -e "  Número:       ${CYAN}$WHATSAPP_NUMBER${NC}"
    echo -e "  Limite Msg:   ${CYAN}$WHATSAPP_LIMIT/dia${NC}"
    echo -e "  Webhook:      ${CYAN}${WEBHOOK_URL}${NC}"
    echo ""
    echo -e "${YELLOW}Configure o webhook na Evolution API:${NC}"
    echo -e "  URL: ${GREEN}${WEBHOOK_URL}${NC}"
    echo -e "  Eventos: QRCODE_UPDATED, CONNECTION_UPDATE, MESSAGES_UPSERT, MESSAGES_UPDATE, SEND_MESSAGE"
    echo ""
fi

echo -e "${BLUE}Acesso:${NC}"
echo -e "  Frontend:  ${GREEN}http://$DOMAIN:5173${NC}"
echo -e "  Backend:   ${GREEN}http://$DOMAIN:8000/api/v1${NC}"
echo -e "  Admin:     ${GREEN}http://$DOMAIN:8000/admin/${NC}"
echo ""
echo -e "${YELLOW}Nota: Para acessar via subdomínio local, adicione ao /etc/hosts:${NC}"
echo -e "  127.0.0.1 ${DOMAIN}"
echo ""
echo -e "${YELLOW}Ou use o header X-Tenant:${NC}"
echo -e "  curl -H 'X-Tenant: $SLUG' http://localhost:8000/api/v1/..."
