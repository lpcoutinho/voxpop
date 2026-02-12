# Comando: seed_database

## Descrição

O comando `seed_database` popula o banco de dados com os dados iniciais necessários para o funcionamento do sistema VoxPop, incluindo planos de assinatura e tags do sistema para todos os tenants.

## O que é criado

1. **Planos de Assinatura** - 3 planos (Basic, Professional, Enterprise) se não existirem
2. **Tags do Sistema** - 3 tags (Lead, Apoiador, Blacklist) para cada tenant existente

## Uso

### Criar tudo (modo padrão)

```bash
python manage.py seed_database
```

### Simular sem fazer alterações

```bash
python manage.py seed_database --dry-run
```

## Planos Criados

### Basic
```python
{
    'name': 'Básico',
    'slug': 'basic',
    'description': 'Plano básico para pequenas campanhas',
    'max_supporters': 1000,
    'max_messages_month': 5000,
    'max_campaigns': 10,
    'max_whatsapp_sessions': 1,
    'price': 99.90,
}
```

### Professional
```python
{
    'name': 'Profissional',
    'slug': 'professional',
    'description': 'Plano profissional para campanhas médias',
    'max_supporters': 10000,
    'max_messages_month': 50000,
    'max_campaigns': 50,
    'max_whatsapp_sessions': 3,
    'price': 299.90,
}
```

### Enterprise
```python
{
    'name': 'Enterprise',
    'slug': 'enterprise',
    'description': 'Plano enterprise para grandes operações',
    'max_supporters': 100000,
    'max_messages_month': 500000,
    'max_campaigns': 200,
    'max_whatsapp_sessions': 10,
    'price': 999.90,
}
```

## Tags do Sistema Criadas

As tags são criadas no schema de cada tenant existente:

### Lead
```python
{
    'name': 'Lead',
    'slug': 'lead',
    'color': '#3b82f6',
    'description': 'Contato inicial que ainda não é apoiador',
    'is_system': True,
    'is_active': True,
}
```

### Apoiador
```python
{
    'name': 'Apoiador',
    'slug': 'apoiaador',  # note: typo proposital para compatibilidade
    'color': '#22c55e',
    'description': 'Apoiador confirmado e engajado',
    'is_system': True,
    'is_active': True,
}
```

### Blacklist
```python
{
    'name': 'Blacklist',
    'slug': 'blacklist',
    'color': '#ef4444',
    'description': 'Contato que não deve ser comunicado',
    'is_system': True,
    'is_active': True,
}
```

## Exemplo de Execução

```bash
$ python manage.py seed_database --dry-run

[DEBUG] Módulo seed_database carregado com sucesso!
================================================================================
SEED BANCO DE DADOS - VoxPop
================================================================================

⚠️  MODO DRY-RUN - Nenhuma alteração será salva

📦 Criando planos de assinatura...
   ✅ Plano "basic" criado
   ✅ Plano "professional" criado
   ✅ Plano "enterprise" criado
   3 planos criados

🏷️  Criando tags do sistema...
   Tenant: João Silva (schema: joao-silva)
      ✅ Tag "Lead" criada
      ✅ Tag "Apoiador" criada
      ✅ Tag "Blacklist" criada

   Tenant: Maria Santos (schema: maria-santos)
      ⏭️  Tag "lead" já existe
      ⏭️  Tag "apoiaador" já existe
      ✅ Tag "Blacklist" criada

   4 tags criadas no total

================================================================================
✓ Seed concluído!
================================================================================

Execute sem --dry-run para aplicar alterações
```

## Quando Usar

### Inicialização do Sistema

Execute logo após criar o banco de dados pela primeira vez:

```bash
# Criar banco
python manage.py migrate_schemas --shared

# Popular com dados iniciais
python manage.py seed_database
```

### Após Criar Novo Tenant

Ao criar um novo tenant (via `create_tenant` ou manual), as tags são criadas automaticamente. Mas se precisar recriar:

```bash
# Recriar tags de um tenant específico
python manage.py create_system_tags --tenant joao-silva
```

### Atualização de Planos

Se você modificou os planos no código e precisa recriá-los:

```bash
# Primeiro deleta os planos existentes (via Django Admin ou SQL)
# Depois executa o seed
python manage.py seed_database
```

## Modo Dry-Run

Sempre use o `--dry-run` primeiro para ver o que será criado:

```bash
python manage.py seed_database --dry-run
```

O modo dry-run:
- ✅ Mostra o que será criado
- ✅ Mostra o que já existe
- ❌ NÃO cria nada

## Ordem de Execução Recomendada

1. **Criar banco e aplicar migrações**
   ```bash
   python manage.py migrate_schemas --shared
   ```

2. **Criar superusuário**
   ```bash
   python manage.py createsuperuser
   ```

3. **Popular dados iniciais**
   ```bash
   python manage.py seed_database
   ```

4. **Criar tenants**
   ```bash
   python manage.py create_tenant --name "João Silva" --slug "joao-silva"
   ```

## Troubleshooting

### Nenhum tenant encontrado

```
⚠️  Nenhum tenant encontrado - crie tenants primeiro
```

**Solução:** Crie tenants primeiro com o comando `create_tenant`.

```bash
python manage.py create_tenant --name "João Silva" --slug "joao-silva"
```

### Erro: "Relation X does not exist"

Isso pode acontecer se as migrações não foram executadas.

**Solução:** Execute as migrações do schema público:

```bash
python manage.py migrate_schemas --shared
```

### Erro: "App core not found"

Se o comando não for encontrado, verifique se `apps.core` está em `INSTALLED_APPS` e se os arquivos `__init__.py` existem.

**Solução:** Verifique a estrutura:
```
apps/core/
├── __init__.py
├── apps.py
├── models.py
└── management/
    ├── __init__.py
    └── commands/
        ├── __init__.py
        └── seed_database.py
```

## Personalização

### Adicionar Novo Plano

Edite o arquivo `apps/core/management/commands/seed_database.py` e adicione no array `plans_data`:

```python
plans_data = [
    # ... planos existentes ...
    {
        'name': 'Mega',
        'slug': 'mega',
        'description': 'Plano mega para operações massivas',
        'max_supporters': 1000000,
        'max_messages_month': 5000000,
        'max_campaigns': 1000,
        'max_whatsapp_sessions': 50,
        'price': 4999.90,
        'is_active': True,
    },
]
```

### Modificar Tags do Sistema

Edite o array `tags_data` no mesmo arquivo:

```python
tags_data = [
    # ... tags existentes ...
    {
        'name': 'VIP',
        'slug': 'vip',
        'color': '#f59e0b',
        'description': 'Apoiador VIP com benefícios especiais',
        'is_system': True,
        'is_active': True,
    },
]
```

## Segurança

### Em Produção

1. **Backup antes de executar**
   ```bash
   pg_dump voxpop_db > backup_before_seed.sql
   ```

2. **Use --dry-run primeiro**
   - Sempre teste em desenvolvimento
   - Use dry-run em produção antes de aplicar

3. **Limite permissões**
   - O comando não deve ser executado por usuários comuns
   - Considere remover o comando em produção se não for necessário

## Veja Também

- [Comando create_tenant](./create-tenant.md) - Cria novos tenants
- [Documentação django-tenants](https://django-tenants.readthedocs.io/)
