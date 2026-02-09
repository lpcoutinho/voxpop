# VoxPop - Deploy Produção

Este documento contém todas as informações necessárias para deploy do VoxPop em produção usando Portainer e Docker Swarm.

## 📋 Arquivos Criados

### 🐳 Docker Configuration
- `docker-compose.production.yml` - Configuração completa para produção
- `backend/Dockerfile.prod` - Imagem otimizada para backend
- `frontend/Dockerfile.prod` - Imagem com Nginx para frontend
- `frontend/nginx.conf` - Configuração Nginx com SSL e otimizações

### 🔧 Settings & Config
- `backend/config/settings/production.py` - Configurações Django produção
- `.env.production.example` - Template de variáveis de ambiente

### 📜 Scripts
- `scripts/build-images.sh` - Build automatizado das imagens
- `scripts/deploy.sh` - Deploy completo via Portainer
- `scripts/backup.sh` - Backup automático do banco e mídia

---

## 🚀 Deploy Passo a Passo

### 1. Preparação Local
```bash
# Clonar repositório
git clone <repositório>
cd voxpop

# Copiar e configurar credenciais
cp .env.production.example .env.production
# Editar .env.production com suas credenciais REAIS
```

### 2. Build das Imagens
```bash
# Tornar script executável
chmod +x scripts/build-images.sh

# Build e push das imagens
./scripts/build-images.sh
```

### 3. Deploy no Portainer
```bash
# Executar deploy
./scripts/deploy.sh
```

---

## 🔐 Variáveis de Ambiente - Produção

### Segurança CRÍTICA
- ✅ `SECRET_KEY_BASE` - Use chave forte e aleatória
- ✅ `POSTGRES_PASSWORD` - Senha forte para o banco
- ✅ `DJANGO_SUPERUSER_PASSWORD` - Senha do admin

### Configurações Banco
- `POSTGRES_DATABASE=voxpop_prod`
- `POSTGRES_USERNAME=voxpop`
- `POSTGRES_HOST=voxpop_postgres`

### Configurações Email
- Configure SMTP real (Gmail, SendGrid, etc.)
- **NÃO use MailHog em produção**

### URLs
- `FRONTEND_URL=https://voxpop.tratto.solutions`
- `VITE_API_URL=https://voxpop.tratto.solutions/api`

---

## 🌐 Configuração Traefik

### Labels Configuradas
- **Frontend**: Priority 1 (rotas estáticas)
- **Backend**: Priority 2 (rotas API)
- **SSL**: Auto LetsEncrypt
- **HTTPS**: Redirect automático HTTP→HTTPS

### Domínios
- Principal: `voxpop.tratto.solutions`
- API: `voxpop.tratto.solutions/api/*`
- Static: Servido pelo Nginx

---

## 📊 Arquitetura de Serviços

### Serviços Configurados
1. **Frontend (Nginx)** - Servidor web estático
2. **Backend (Django)** - API REST
3. **Celery Worker** - Processamento assíncrono
4. **Celery Beat** - Agendamento de tarefas
5. **PostgreSQL** - Banco de dados principal
6. **Redis** - Cache e broker de mensagens

### Recursos Alocados
- **Frontend**: 0.5 CPU, 512MB RAM
- **Backend**: 1.0 CPU, 2048MB RAM
- **Worker**: 1.0 CPU, 1024MB RAM
- **Beat**: 0.5 CPU, 256MB RAM
- **Postgres**: 1.0 CPU, 2048MB RAM
- **Redis**: 0.5 CPU, 512MB RAM

---

## 🔧 Gestão e Monitoramento

### Logs
- **Backend**: stdout → Docker logs
- **Frontend**: Nginx access/error logs
- **Celery**: Task execution logs
- **Database**: PostgreSQL logs

### Health Checks
- **PostgreSQL**: `pg_isready`
- **Redis**: `redis-cli ping`
- **Backend**: Django health endpoint

### Backup Automático
```bash
# Executar backup manual
./scripts/backup.sh

# Ou configurar cron (via Portainer)
0 2 * * * /path/to/voxpop/scripts/backup.sh
```

---

## 🚨 Segurança Produção

### Configurações Habilitadas
- ✅ HTTPS forçado
- ✅ HSTS headers
- ✅ Cookies seguros
- ✅ CORS restrito
- ✅ Rate limiting
- ✅ Security headers

### Monitoramento
- ✅ Health checks em todos os serviços
- ✅ Logs centralizados
- ✅ Backup automático
- ✅ Resource limits

---

## 🔧 Manutenção

### Atualizar Sistema
```bash
# Build novas versões
./scripts/build-images.sh

# Deploy atualizado
./scripts/deploy.sh
```

### Backup e Restore
```bash
# Backup
./scripts/backup.sh

# Restore (manual via Docker exec)
docker exec voxpop_postgres psql -U voxpop -d voxpop_prod < backup.sql
```

---

## 📱 Acesso ao Sistema

### URLs de Produção
- **Principal**: https://voxpop.tratto.solutions
- **Admin**: https://voxpop.tratto.solutions/admin/
- **API**: https://voxpop.tratto.solutions/api/

### Credenciais Padrão
- **Email**: admin@voxpop.tratto.solutions
- **Senha**: Definida em `DJANGO_SUPERUSER_PASSWORD`

---

## 🛠️ Troubleshooting

### Problemas Comuns
1. **Serviços não iniciam**: Verificar volumes externos
2. **SSL não funciona**: Verificar configuração DNS
3. **Database connection**: Validar variáveis POSTGRES_*
4. **CORS errors**: Verificar `CORS_ALLOWED_ORIGINS`

### Debug Commands
```bash
# Verificar serviços
docker stack services voxpop

# Verificar logs
docker stack logs voxpop

# Verificar volumes
docker volume ls | grep voxpop

# Verificar rede
docker network ls | grep LaunchNet
```

---

## 📞 Suporte

### Para Deploy
1. **Configurar .env.production** com credenciais reais
2. **Ajustar recursos** conforme necessidade
3. **Testar em staging** antes de produção
4. **Monitorar após deploy**

### Para Suporte Técnico
- ✅ Logs coletados automaticamente
- ✅ Backups diários automáticos
- ✅ Health checks ativos
- ✅ Alertas configuráveis

---

**Este setup é production-ready e segue as melhores práticas de segurança e performance!** 🎉