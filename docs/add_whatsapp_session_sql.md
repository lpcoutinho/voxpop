# Como Adicionar Sessões WhatsApp Manualmente (SQL)

Como o VoxPop utiliza **Multi-Tenancy** com isolamento de schemas, a inserção de dados deve ser feita no schema específico do cliente (ex: `demo`, `campanha_x`).

## Dados Necessários
Para cada instância na **Evolution API**, você precisará de:
1. **instance_name**: O nome da instância configurada na API.
2. **access_token**: O token de autenticação gerado pela API para essa instância.

---

## Passo 1: Acessar o Banco de Dados

Acesse o terminal do PostgreSQL através do Docker:

```bash
docker compose exec db psql -U voxpop -d voxpop_db
```

---

## Passo 2: Executar o Comando SQL

Substitua os valores entre `< >` pelos dados reais e defina o schema correto no comando `SET search_path`.

```sql
-- 1. Definir o schema do cliente (Ex: demo, cliente_01, etc)
SET search_path TO demo;

-- 2. Inserir a nova sessão
INSERT INTO whatsapp_whatsappsession (
    created_at,
    updated_at,
    name,
    instance_name,
    access_token,
    status,
    daily_message_limit,
    messages_sent_today,
    is_healthy,
    is_active,
    phone_number,
    webhook_url
) VALUES (
    NOW(),                          -- created_at
    NOW(),                          -- updated_at
    'Nome da Sessão',               -- nome visível no painel
    'instancia_xyz',                -- instance_name da Evolution API
    'token_secreto_aqui',           -- access_token da Evolution API
    'disconnected',                 -- status inicial
    1000,                           -- limite diário
    0,                              -- mensagens enviadas hoje
    false,                          -- is_healthy
    true,                           -- is_active
    '',                             -- phone_number (será preenchido no login)
    'http://backend:8000/api/v1/whatsapp/webhook/instancia_xyz/' -- URL do Webhook
);
```

---

## Passo 3: Verificação no Frontend

1. Acesse o VoxPop no navegador.
2. Vá para a página de **WhatsApp**.
3. A sessão aparecerá na lista. Ao clicar em **"Conectar"**, o sistema usará o `instance_name` e `access_token` configurados para buscar o QR Code da API e permitir o login.

---

## Dica: Criar via Django Shell (Mais Seguro)

Se preferir não lidar com SQL puro, você pode usar o shell do Django, que já trata as URLs de webhook automaticamente:

```python
# docker compose exec backend python manage.py shell
from django_tenants.utils import schema_context
from apps.whatsapp.models import WhatsAppSession

with schema_context('demo'):
    WhatsAppSession.objects.create(
        name="Comercial",
        instance_name="instancia_01",
        access_token="seu_token_aqui",
        daily_message_limit=1500,
        webhook_url="http://backend:8000/api/v1/whatsapp/webhook/instancia_01/"
    )
```
