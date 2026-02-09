# Checklist Produção - VoxPop

## ✅ Verificações Antes do Deploy

### 1. Scripts de Deploy
- [x] `scripts/create-tenant.sh` - Criar tenant via banco de dados
- [x] `scripts/build-images.sh` - Build imagens Docker
- [x] `scripts/deploy.sh` - Deploy via Portainer
- [x] `scripts/backup.sh` - Backup automático

### 2. Configurações Docker
- [x] `docker-compose.production.yml` - Stack produção
- [x] `backend/Dockerfile.prod` - Imagem backend
- [x] `frontend/Dockerfile.prod` - Imagem frontend + Nginx
- [x] `frontend/nginx.conf` - Config Nginx com SSL

### 3. Configurações Backend
- [x] `backend/config/settings/production.py` - Settings produção
- [x] `.env.production.example` - Template variáveis ambiente

### 4. Dados Testados
- [x] Tenant criado com sucesso
- [x] Schema PostgreSQL criado
- [x] Migrações aplicadas
- [x] Dados iniciais criados (tags, segmentos, templates)
- [x] Sessão WhatsApp criada

### 5. Planos Disponíveis
- [x] Free Tier (ID: 1)

---

## 🔧 Configurações Necessárias em Produção

### 1. Arquivo `.env.production`

```bash
# Copiar template
cp .env.production.example .env.production

# Editar com valores REAIS:
# - SECRET_KEY_BASE (gerar nova chave)
# - POSTGRES_PASSWORD (senha forte)
# - DJANGO_SUPERUSER_PASSWORD (senha admin)
# - SMTP credentials (email real)
```

### 2. Dominios DNS

```
voxpop.tratto.solutions → A record para IP do servidor
www.voxpop.tratto.solutions → CNAME para voxpop.tratto.solutions
```

### 3. Traefik / Portainer

- Configurar Traefik para SSL automático (LetsEncrypt)
- Configurar rede `LaunchNet` no Docker Swarm
- Ajustar recursos conforme necessário

---

## 📋 Scripts Disponíveis

### Criar Tenant em Produção

```bash
# SSH no servidor
ssh usuario@servidor

# Entrar no diretório do projeto
cd /var/www/voxpop

# Executar serviço admin
docker exec voxpop_backend python manage.py shell

# Ou usar script adaptado:
./scripts/create-tenant-prod.sh "Nome" "email@exemplo.com"
```

### Backup Manual

```bash
# Backup completo
./scripts/backup.sh
```

### Ver Logs

```bash
# Backend
docker service logs -f voxpop_backend --tail 100

# Celery
docker service logs -f voxpop_celery --tail 100

# Todos
docker stack services voxpop
```

---

## ⚠️ Observações Importantes

### Script create-tenant.sh

1. **Funciona em dev e prod** - usa variáveis de ambiente
2. **Atualiza tenant existente** - não falha se já existe
3. **Reutiliza usuário** - se email já cadastrado
4. **Adiciona WhatsApp** - sempre cria/atualiza sessão

### Uso em Produção

```bash
# No servidor de produção
docker exec voxpop_backend python manage.py shell << EOF
import django
django.setup()

from django_tenants.utils import schema_context
from apps.tenants.models import Client
from apps.accounts.models import User
from apps.whatsapp.models import WhatsAppSession

# Criar ou atualizar tenant
# ... (código do script)
EOF
```

---

## ✨ Próximos Passos

1. **Configurar .env.production** com credenciais reais
2. **Build e push das imagens** Docker
3. **Deploy via Portainer** usando `scripts/deploy.sh`
4. **Testar crição de tenant** em produção
5. **Configurar cron job** para backup diário

---

## 🔒 Segurança

- [ ] Usar SECRET_KEY com 128+ caracteres
- [ ] DEBUG=False em produção
- [ ] HTTPS forçado (Traefik)
- [ ] Rate limiting configurado
- [ ] Senhas fortes ( banco, admin, smtp )
- [ ] BACKUP automatizado
- [ ] Logs centralizados

---

## 📊 Monitoramento

- Health checks ativos (docker-compose)
- Logs stdout para Docker
- Sentry para erros (configurar DSN)
- Backup diário automatizado
