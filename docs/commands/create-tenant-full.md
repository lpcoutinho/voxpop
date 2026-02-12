# Comando: create_tenant_full

## Descrição

O comando `create_tenant_full` cria um novo tenant completo (cliente/campanha) no sistema VoxPop com todas as configurações necessárias, incluindo a integração com a Evolution API para WhatsApp.

> **Nota:** Este comando substitui o comando nativo `create_tenant` do django-tenants, criando um tenant completo com todas as integrações.

## O que é criado

1. **Tenant (Client)** - Schema PostgreSQL separado para isolamento completo de dados
2. **Domínio** - Domínio de acesso ao tenant
3. **Sessão WhatsApp** - Instância na Evolution API com webhook configurado
4. **Tags do Sistema** - Tags padrão (Lead, Apoiador, Blacklist) para o tenant

## Requisitos

- Python 3.12+
- Django com django-tenants configurado
- Evolution API rodando e acessível
- Variáveis de ambiente configuradas:
  - `EVOLUTION_API_URL` - URL da Evolution API (ex: `http://localhost:8080`)
  - `EVOLUTION_API_KEY` - Chave de API da Evolution
  - `BASE_URL` - URL base do backend (ex: `http://localhost:8000`)

## Uso

### Modo Interativo (Recomendado)

Execute o comando sem argumentos para preencher os dados interativamente:

```bash
python manage.py create_tenant
```

O comando vai perguntar:

```
Nome da organização/político: João Silva
Slug (pressione Enter para "joão-silva"):
Domínio (pressione Enter para "joão-silva.localhost"):
E-mail (opcional): joao@example.com
Telefone (opcional): 11999999999
CNPJ (opcional): 12.345.678/0001-90
```

### Modo com Argumentos

Especifique todos os dados via linha de comando:

```bash
python manage.py create_tenant \
  --name "Rodrigo Noel" \
  --slug "rodrigo-noel" \
  --domain "noel.voxpop.tarttosolutions.com" \
  --plan "professional" \
  --email "noel@noel.com" \
  --phone "11999999999" \
  --session-name "Noel01"
```

### Modo Dry-Run

Simule a criação sem fazer alterações:

```bash
python manage.py create_tenant_full --dry-run --name "Teste"
```

### Registrar Instância Existente

Quando você já criou a instância na Evolution API e quer apenas registrar no banco:

```bash
python manage.py create_tenant_full \
  --name "Rodrigo Noel" \
  --slug "rodrigo-noel" \
  --domain "noel.voxpop.tarttosolutions.com" \
  --plan "professional" \
  --email "noel@noel.com" \
  --phone "11999999999" \
  --session-name "Noel01" \
  --existing-instance \
  --evolution-token "D6E2DB28378B-4F75-9C7C-EEA14D209BCC"
```

> **Nota:** Ao usar `--existing-instance`, o comando NÃO tenta criar a nova instância na Evolution API. Apenas registra no banco de dados.

### Sem WhatsApp

Crie apenas o tenant sem a integração WhatsApp:

```bash
python manage.py create_tenant_full \
  --name "João Silva" \
  --slug "joao-silva" \
  --no-whatsapp
```

## Argumentos

| Argumento | Tipo | Descrição | Obrigatório |
|-----------|------|-----------|-------------|
| `--name` | string | Nome da organização/político | ❌ (pergunta se não informado) |
| `--slug` | string | Slug único do tenant (usado no schema_name) | ❌ (gera do nome se não informado) |
| `--domain` | string | Domínio do tenant (ex: joao.localhost) | ❌ (gera do slug se não informado) |
| `--plan` | string | Plano de assinatura (basic/professional/enterprise) | ❌ (default: basic) |
| `--email` | string | E-mail de contato | ❌ |
| `--phone` | string | Telefone de contato | ❌ |
| `--document` | string | CNPJ da organização | ❌ |
| `--session-name` | string | Nome da sessão WhatsApp | ❌ (usa o slug se não informado) |
| `--evolution-token` | string | Token customizado para a Evolution API | ❌ (gera automaticamente se não informado) |
| `--existing-instance` | flag | Registra instância já existente (não cria nova na API) | ❌ |
| `--no-whatsapp` | flag | Não criar instância WhatsApp | ❌ |
| `--dry-run` | flag | Simula a execução sem salvar | ❌ |

## Planos Disponíveis

### Basic
- **Apoiadores:** 1.000
- **Mensagens/mês:** 5.000
- **Campanhas simultâneas:** 10
- **Sessões WhatsApp:** 1
- **Preço:** R$ 99,90/mês

### Professional
- **Apoiadores:** 10.000
- **Mensagens/mês:** 50.000
- **Campanhas simultâneas:** 50
- **Sessões WhatsApp:** 3
- **Preço:** R$ 299,90/mês

### Enterprise
- **Apoiadores:** 100.000
- **Mensagens/mês:** 500.000
- **Campanhas simultâneas:** 200
- **Sessões WhatsApp:** 10
- **Preço:** R$ 999,90/mês

## Exemplo de Execução

```bash
$ python manage.py create_tenant \
  --name "Campanha João Silva" \
  --slug "joao-silva" \
  --domain "joao.localhost" \
  --plan "basic" \
  --email "joao@example.com"

================================================================================
CRIAR TENANT - VoxPop
================================================================================

✓ Plano: Básico

================================================================================
Resumo da Criação:
================================================================================
Nome: Campanha João Silva
Slug/Schema: joao-silva
Domínio: joao.localhost
Plano: Básico
E-mail: joao@example.com
Sessão WhatsApp: joao-silva

Confirma a criação do tenant? [y/N]: y

📦 Criando tenant...
   ✅ Tenant criado (schema: joao-silva)
🌐 Criando domínio...
   ✅ Domínio criado: joao.localhost
📱 Criando instância WhatsApp...
   ✅ Instância criada na Evolution API
   ✅ Sessão criada no banco
🏷️  Criando tags do sistema...
   ✅ 3 tags criadas

================================================================================
✅ TENANT CRIADO COM SUCESSO!
================================================================================

📋 Dados do Tenant:
   Nome: Campanha João Silva
   Schema: joao-silva
   Domínio: joao.localhost
   Plano: Básico

📱 Sessão WhatsApp:
   Nome: Campanha João Silva - WhatsApp
   Instância: joao-silva
   Status: Desconectado

================================================================================
🔗 URL DO WEBHOOK - CONFIGURE NA EVOLUTION API
================================================================================

http://localhost:8000/api/whatsapp/webhook/evolution/joao-silva/

================================================================================

Para configurar na Evolution API:
   1. Acesse a instância: joao-silva
   2. Configure o webhook com a URL acima
   3. Gere o QR Code e conecte o WhatsApp

🏷️  3 tags do sistema criadas
```

## URL do Webhook

A URL retornada pelo comando deve ser configurada na Evolution API para receber eventos:

```
http://localhost:8000/api/whatsapp/webhook/evolution/{instance_name}/
```

### Eventos Recebidos

- `QRCODE_UPDATED` - Atualização do QR Code
- `CONNECTION_UPDATE` - Mudança no status de conexão
- `MESSAGES_UPSERT` - Nova mensagem recebida
- `MESSAGES_UPDATE` - Atualização de mensagem
- `SEND_MESSAGE` - Confirmação de envio

### Configurando na Evolution API

1. Acesse a interface da Evolution API (normalmente `http://localhost:8080`)
2. Localize a instância criada
3. Vá em "Settings" ou "Webhook"
4. Cole a URL retornada pelo comando
5. Configure os eventos desejados
6. Salve a configuração

## Tags do Sistema

O comando cria automaticamente 3 tags no schema do tenant:

### Lead
- **Slug:** `lead`
- **Cor:** #3B82F6 (azul)
- **Descrição:** Contato inicial - ainda não é apoiador

### Apoiador
- **Slug:** `apoiador`
- **Cor:** #22C55E (verde)
- **Descrição:** Contato engajado - apoiador confirmado

### Blacklist
- **Slug:** `blacklist`
- **Cor:** #EF4444 (vermelho)
- **Descrição:** Não contatar - excluído de campanhas

Essas tags são marcadas como `is_system=True` e **não podem ser deletadas**, apenas desativadas.

## Pós-Criação

Após criar o tenant:

1. **Conecte o WhatsApp**
   - Gere o QR Code via API ou admin
   - Escaneie com o celular
   - Aguarde a conexão ser estabelecida

2. **Criar Usuários**
   - Crie usuários com acesso ao tenant via Django Admin
   - Associe os usuários ao tenant via TenantMembership

3. **Importar Apoiadores**
   - Use o sistema de importação em lote
   - Os apoiadores serão criados no schema do tenant

4. **Criar Campanhas**
   - Crie campanhas para engajar os apoiadores
   - Configure mensagens e templates

## Token da Evolution API

### O que é o Token?

Cada instância da Evolution API possui um token de acesso (API Key) que:
- Autentica requisições à API
- Permite enviar mensagens
- Permite configurar webhooks
- Permite verificar status da conexão

### Token Gerado Automaticamente

Por padrão, se você não informar um token, a Evolution API gera um automaticamente:

```bash
# Token gerado automaticamente
python manage.py create_tenant --name "João Silva" --slug "joao-silva"
```

O comando mostrará:
```
🔑 Token: a1b2c3d4e5...***
```

### Token Customizado

Você pode fornecer seu próprio token para a instância:

```bash
# Com token customizado
python manage.py create_tenant \
  --name "João Silva" \
  --slug "joao-silva" \
  --evolution-token "meu-token-secreto-123"
```

**Quando usar token customizado:**
- Para facilitar identificação da instância
- Para integrar com sistemas externos
- Para ter tokens mais memoráveis
- Para ambientes específicos (dev, staging, prod)

### Onde Encontrar o Token

Após criar o tenant, você pode encontrar o token de 3 formas:

1. **Na saída do comando**
   ```
   🔑 Token: a1b2c3d4e5...***
   ```

2. **No Django Admin**
   - Acesse: http://localhost:8000/admin
   - Navegue para: WhatsApp → Sessões WhatsApp
   - Encontre a sessão e veja o "Access Token"

3. **Direto na Evolution API**
   - Acesse a interface da Evolution API
   - Encontre a instância
   - Copie o token/instance token

### Usando o Token

O token é usado no cabeçalho das requisições para a Evolution API:

```python
headers = {
    'apikey': 'seu-token-aqui',
    'Content-Type': 'application/json'
}
```

## Troubleshooting

### Erro: "Plano X não encontrado"

Verifique se os planos foram criados no banco:

```bash
python manage.py seed_database
```

### Erro: "Slug deve conter apenas letras, números e hífens"

O slug não pode conter caracteres especiais. Use apenas:
- Letras minúsculas (a-z)
- Números (0-9)
- Hífens (-)

Exemplo: `joao-silva-2024`

### Erro: "Schema já existe"

Cada tenant deve ter um schema_name único. Verifique se já existe um tenant com o mesmo slug.

### Erro na conexão com Evolution API

Verifique:
1. Se a Evolution API está rodando
2. Se `EVOLUTION_API_URL` está correto no `.env`
3. Se `EVOLUTION_API_KEY` está configurado
4. Se há conectividade de rede

### Webhook não está recebendo eventos

Verifique:
1. Se a URL está configurada corretamente na Evolution API
2. Se o `BASE_URL` no `.env` está correto
3. Se a aplicação está acessível externamente
4. Se o firewall não está bloqueando as requisições

## Segurança

### Proteção dos Tokens

Os tokens da Evolution API são credenciais sensíveis:

**❌ NÃO FAÇA:**
- ❌ Commitar tokens no repositório Git
- ❌ Compartilhar tokens em canais públicos (Slack, Discord, etc)
- ❌ Usar tokens fracos (ex: "123456", "token")
- ❌ Reutilizar o mesmo token para múltiplas instâncias em produção
- ❌ Exibir o token completo em logs

**✅ FAÇA:**
- ✅ Usar tokens fortes e únicos por instância
- ✅ Armazenar tokens em variáveis de ambiente
- ✅ Rotacionar tokens periodicamente
- ✅ Usar tokens diferentes para dev/teste e produção
- ✅ Registrar quando tokens são criados/modificados
- ✅ Exibir apenas os primeiros caracteres dos tokens em logs

### Exemplo de Token Seguro

```bash
# ❌ Token fraco
python manage.py create_tenant --evolution-token "meutoken"

# ✅ Token forte
python manage.py create_tenant --evolution-token "voxp_joao_2024_a7f9c3e2d8b1x4z6"
```

### Em Produção

1. **Use HTTPS**
   - Configure `BASE_URL` com HTTPS
   - Tenha um certificado SSL válido

2. **Limite acesso por IP**
   - Configure a Evolution API para aceitar webhooks apenas do IP do servidor

3. **Use secrets fortes**
   - API Keys da Evolution devem ser segredas
   - Gere tokens diferentes por instância se possível

4. **Monitore logs**
   - Acompanhe os logs de webhooks
   - Configure alertas para falhas

## Veja Também

- [Comando seed_database](./seed-database.md) - Cria planos e tags do sistema
- [Documentação da Evolution API](https://doc.evolution-api.com/)
- [Documentação django-tenants](https://django-tenants.readthedocs.io/)
