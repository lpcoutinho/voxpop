# Comandos de Gerenciamento - VoxPop

Documentação dos comandos customizados do Django para gerenciar o sistema VoxPop.

## Comandos Disponíveis

### [create_tenant_full](./create-tenant-full.md)
Cria um novo tenant completo (cliente/campanha) com integração WhatsApp completa.

```bash
python manage.py create_tenant_full
```

**O que faz:**
- Cria tenant com schema PostgreSQL separado
- Configura domínio para acesso
- Cria instância na Evolution API
- Configura webhook automaticamente
- Cria tags do sistema (Lead, Apoiador, Blacklist)
- **Retorna a URL do webhook para configurar na Evolution API**

**Quando usar:**
- Ao cadastrar novo cliente/campanha
- Ao configurar nova organização política

> **Nota:** Este comando substitui o `create_tenant` nativo do django-tenants

---

### [seed_database](./seed-database.md)
Popula o banco de dados com dados iniciais do sistema.

```bash
python manage.py seed_database
```

**O que faz:**
- Cria 3 planos de assinatura (Basic, Professional, Enterprise)
- Cria tags do sistema para todos os tenants existentes

**Quando usar:**
- Na inicialização do sistema
- Após executar migrações
- Ao criar novo tenant (via create_tenant já cria automaticamente)

## Fluxo de Trabalho Recomendado

### Inicialização do Sistema

```bash
# 1. Criar banco de dados
createdb voxpop_db

# 2. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# 3. Aplicar migrações
python manage.py migrate_schemas --shared

# 4. Criar superusuário
python manage.py createsuperuser

# 5. Popular dados iniciais
python manage.py seed_database

# 6. Criar primeiro tenant
python manage.py create_tenant_full
```

### Criação de Novo Tenant

```bash
# 1. Criar o tenant
python manage.py create_tenant_full \
  --name "João Silva" \
  --slug "joao-silva" \
  --domain "joao.voxpop.com.br" \
  --plan "basic"

# 2. Configurar o webhook (URL retornada pelo comando)
# Acesse a Evolution API e configure a URL retornada

# 3. Conectar o WhatsApp
# Gere o QR Code e escaneie com o celular
```

## Modo Dry-Run

Sempre que possível, use `--dry-run` para testar antes de aplicar:

```bash
# Testar criação de tenant
python manage.py create_tenant --dry-run --name "Teste"

# Testar seed do banco
python manage.py seed_database --dry-run
```

## Flags Comuns

| Flag | Descrição | Disponível em |
|------|-----------|---------------|
| `--dry-run` | Simula sem salvar | `create_tenant_full`, `seed_database` |
| `--existing-instance` | Registra instância já existente (não cria nova na API) | `create_tenant_full` |
| `--no-whatsapp` | Não cria instância WhatsApp | `create_tenant_full` |
| `--plan SLUG` | Define o plano | `create_tenant_full` |
| `--help` | Mostra ajuda do comando | Todos |

## Troubleshooting

### Comando não encontrado

```bash
# Verifique se o app está em INSTALLED_APPS
python manage.py shell
>>> from django.conf import settings
>>> 'apps.tenants' in settings.INSTALLED_APPS
True
```

### Erro de permissão

```bash
# Verifique permissões do banco
GRANT ALL PRIVILEGES ON DATABASE voxpop_db TO voxpop;
```

### Erro na Evolution API

```bash
# Verifique se está rodando
curl http://localhost:8080

# Verifique configurações
echo $EVOLUTION_API_URL
echo $EVOLUTION_API_KEY
```

## Estrutura de Diretórios

```
apps/
├── core/
│   └── management/commands/
│       └── seed_database.py
└── tenants/
    └── management/commands/
        └── create_tenant_full.py
```

## Próximos Passos

- Veja a documentação específica de cada comando para detalhes
- Consulte a [documentação da Evolution API](https://doc.evolution-api.com/)
- Leia sobre [django-tenants](https://django-tenants.readthedocs.io/)

## Suporte

Para problemas ou dúvidas:
1. Verifique os logs da aplicação
2. Consulte a documentação específica do comando
3. Abra uma issue no repositório
