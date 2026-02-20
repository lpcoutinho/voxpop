# 🚀 Guia de Deploy - VoxPop em Produção

Guia completo para fazer deploy da aplicação VoxPop em produção usando Docker Swarm, Portainer e Traefik.

## 📋 Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Preparação da VPS](#preparação-da-vps)
3. [Build das Imagens Docker](#build-das-imagens-docker)
4. [Configuração Inicial](#configuração-inicial)
5. [Deploy via Portainer](#deploy-via-portainer)
6. [Comandos Úteis](#comandos-úteis)
7. [Monitoramento e Logs](#monitoramento-e-logs)
8. [Troubleshooting](#troubleshooting)

---

## 📦 Pré-requisitos

### Na VPS:
- ✅ Docker Swarm configurado e funcionando
- ✅ Portainer instalado e acessível
- ✅ Traefik configurado com Let's Encrypt
- ✅ Rede `LaunchNet` criada
- ✅ DNS apontando: `voxpop.tratto.solutions` → IP da VPS

### Na Máquina Local:
- ✅ Docker instalado
- ✅ Acesso SSH à VPS
- ✅ Código do projeto clonado

---

## 🔧 Preparação da VPS

### 1. Criar Volumes Externos

SSH na VPS e execute:

```bash
# Conecte-se à VPS
ssh usuario@sua-vps.com

# Criar volumes necessários (NOTA: PostgreSQL é EXTERNO, não criamos volume para ele)
docker volume create voxpop_redis_data
docker volume create voxpop_logs

# Verificar volumes criados
docker volume ls | grep voxpop
```

Saída esperada:
```
voxpop_redis_data
voxpop_logs
```

**IMPORTANTE:** Esta stack usa PostgreSQL **EXISTENTE/EXTERNO**, não cria um container de banco. Certifique-se de configurar a variável `POSTGRES_HOST` no Portainer apontando para o servidor PostgreSQL existente.

### 2. Verificar Rede LaunchNet

```bash
# Verificar se a rede existe
docker network ls | grep LaunchNet

# Se não existir, criar (mas no seu caso já deve existir)
docker network create -d overlay LaunchNet
```

### 3. Configurar Variáveis de Ambiente no Portainer

No Portainer, vá em:
**Stacks** → **Add stack** → **Environment variables**

Ou crie um arquivo `.env.production` localmente e use no deploy:

```bash
# ==========================================
# SEGURANÇA - GERE CHAVES SEGURAS!
# ==========================================

# Django Secret Key (Mínimo 128 caracteres)
SECRET_KEY=seu-secret-key-aqui-minimo-128-caracteres-aleatorios-mude-isso-imediatamente

# ==========================================
# POSTGRESQL EXTERNO (OBRIGATÓRIO)
# ==========================================

# Hostname ou IP do servidor PostgreSQL existente
POSTGRES_HOST=postgres.meudominio.com
# OU use IP: POSTGRES_HOST=192.168.1.100
# OU use nome de serviço Docker se estiver na mesma rede: POSTGRES_HOST=nome-do-servico-postgres

POSTGRES_PORT=5432
POSTGRES_DB=voxpop_prod
POSTGRES_USER=voxpop
POSTGRES_PASSWORD=sua-senha-postgres-aqui-mude-isso-imediatamente

# ==========================================
# EVOLUTION API (WhatsApp)
# ==========================================

EVOLUTION_API_URL=https://evolution.tratto.solutions
EVOLUTION_API_KEY=sua-chave-api-evolution-aqui

# ==========================================
# EMAIL/SMTP (Opcional)
# ==========================================

MAILER_SENDER_EMAIL=seu-email@gmail.com
SMTP_DOMAIN=gmail.com
SMTP_ADDRESS=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-de-app-do-google

# ==========================================
# NOTAS IMPORTANTES:
# ==========================================
#
# 1. Gere SECRET_KEY com: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
#
# 2. POSTGRES_HOST deve apontar para o servidor PostgreSQL EXISTENTE.
#    - Verifique se o banco voxpop_prod já foi criado
#    - Verifique se o usuário voxpop tem permissões
#    - Verifique se o firewall permite conexão
#
# 3. Para SMTP do Gmail, use "App Password":
#    - Google Account → Security → 2-Step Verification → App passwords
#
# 4. NUNCA comite este arquivo com credenciais reais!
#
```

**Gerar SECRET_KEY seguro:**

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 🏗️ Build das Imagens Docker

Na sua **máquina local**, navegue até o projeto:

```bash
cd /path/to/voxpop
```

### Build da Imagem Backend

```bash
cd backend

# Build com tag específica
docker build -f Dockerfile.prod -t lpcoutinho/voxpop-backend:latest .

# Push para Docker Hub (ou seu registry)
docker push lpcoutinho/voxpop-backend:latest
```

### Build da Imagem Frontend

```bash
cd ../frontend

# Build com tag específica
docker build -f Dockerfile.prod -t lpcoutinho/voxpop-frontend:latest .

# Push para Docker Hub
docker push lpcoutinho/voxpop-frontend:latest
```

### Script Automatizado (Opcional)

Você pode usar o script `build-images.sh`:

```bash
chmod +x build-images.sh
./build-images.sh
```

---

## 🚀 Deploy via Portainer

### Método 1: Via Interface Web

1. **Acesse o Portainer**
   ```
   https://portainer.seudominio.com
   ```

2. **Adicionar nova Stack**
   - Menu lateral: **Stacks** → **Add stack**
   - Nome: `voxpop-production`
   - Escolha: **Upload from git repository** ou **Web editor**

3. **Configurar Stack**

   **Editor Web:**
   - Copie o conteúdo de `docker-compose.stack.yml`
   - Cole no editor

   **Git Repository:**
   - Repository URL: `https://github.com/seu-usuario/voxpop.git`
   - Compose path: `docker-compose.stack.yml`

4. **Adicionar Environment Variables**

   Clique em **"Editor for environment variables"** e adicione:

   ```yaml
   SECRET_KEY: sua-secret-key-aqui
   POSTGRES_PASSWORD: sua-senha-postgres-aqui
   EVOLUTION_API_URL: https://evolution.tratto.solutions
   EVOLUTION_API_KEY: sua-chave-api-evolution
   MAILER_SENDER_EMAIL: seu-email@gmail.com
   SMTP_DOMAIN: gmail.com
   SMTP_ADDRESS: smtp.gmail.com
   SMTP_PORT: 587
   SMTP_USERNAME: seu-email@gmail.com
   SMTP_PASSWORD: sua-senha-app
   ```

5. **Deploy**
   - Clique em **"Deploy the stack"**
   - Aguarde alguns minutos
   - Verifique se todos os serviços estão "green"

### Método 2: Via SSH na VPS

```bash
# SSH na VPS
ssh usuario@sua-vps.com

# Navegar até diretório de stacks
cd /opt/stacks/voxpop

# Copiar docker-compose.stack.yml para a VPS
# (via scp ou git clone)

# Fazer deploy
docker stack deploy -c docker-compose.stack.yml voxpop

# Verificar status
docker stack ps voxpop
docker stack services voxpop
```

---

## 📊 Verificar Deploy

### 1. Verificar Serviços

```bash
# Listar serviços da stack
docker stack services voxpop

# Saída esperada:
# ID             NAME                       REPLICAS   IMAGE
# abc123         voxpop_voxpop-frontend     1/1        lpcoutinho/voxpop-frontend:latest
# def456         voxpop_voxpop-backend      1/1        lpcoutinho/voxpop-backend:latest
# ghi789         voxpop_voxpop-celery       1/1        lpcoutinho/voxpop-backend:latest
# jkl012         voxpop_voxpop-celery-beat  1/1        lpcoutinho/voxpop-backend:latest
# mno345         voxpop_voxpop-redis        1/1        redis:7-alpine
#
# NOTA: voxpop-postgres NÃO aparece nesta lista pois usamos PostgreSQL EXTERNO
```

### 2. Verificar Logs

```bash
# Frontend
docker logs $(docker ps -q -f name=voxpop-frontend) --tail 100 -f

# Backend
docker logs $(docker ps -q -f name=voxpop-backend) --tail 100 -f

# Celery
docker logs $(docker ps -q -f name=voxpop-celery) --tail 100 -f

# Celery Beat
docker logs $(docker ps -q -f name=voxpop-celery-beat) --tail 100 -f
```

### 3. Verificar Saúde dos Serviços

```bash
# Ver todos os containers
docker ps -a

# Verificar health checks
docker inspect --format='{{.State.Health.Status}}' $(docker ps -q -f name=voxpop-backend)
```

### 4. Acessar Aplicação

- **Frontend**: https://voxpop.tratto.solutions
- **API**: https://voxpop.tratto.solutions/api/v1/
- **Admin**: https://voxpop.tratto.solutions/admin/

---

## 🔄 Atualizar Deploy

### Quando Alterar Código

1. **Build e push novas imagens**
   ```bash
   # Backend
   cd backend
   docker build -f Dockerfile.prod -t lpcoutinho/voxpop-backend:latest .
   docker push lpcoutinho/voxpop-backend:latest

   # Frontend
   cd ../frontend
   docker build -f Dockerfile.prod -t lpcoutinho/voxpop-frontend:latest .
   docker push lpcoutinho/voxpop-frontend:latest
   ```

2. **Forçar update no Swarm**
   ```bash
   # SSH na VPS
   ssh usuario@sua-vps.com

   # Atualizar stack
   docker stack deploy -c docker-compose.stack.yml voxpop

   # Ou via Portainer: Stacks → voxpop → Update stack
   ```

3. **Verificar atualização**
   ```bash
   docker stack ps voxpop
   ```

---

## 🛠️ Comandos Úteis

### Gerenciar Stack

```bash
# Ver status da stack
docker stack ps voxpop

# Ver serviços
docker stack services voxpop

# Remover stack (CUIDADO!)
docker stack rm voxpop

# Re-deploy stack
docker stack deploy -c docker-compose.stack.yml voxpop
```

### Gerenciar Serviços Individuais

```bash
# Escalar serviços
docker service scale voxpop_voxpop-celery=2

# Ver logs de serviço específico
docker service logs voxpop_voxpop-backend --tail 100 -f

# Reiniciar serviço
docker service update --force voxpop_voxpop-backend
```

### Acessar Container para Debug

```bash
# Listar containers
docker ps

# Entrar no container backend
docker exec -it $(docker ps -q -f name=voxpop-backend) bash

# Entrar no container frontend
docker exec -it $(docker ps -q -f name=voxpop-frontend) sh

# Executar comandos Django
docker exec -it $(docker ps -q -f name=voxpop-backend) python manage.py shell

# Criar superuser
docker exec -it $(docker ps -q -f name=voxpop-backend) python manage.py createsuperuser

# Rodar migrações manualmente
docker exec -it $(docker ps -q -f name=voxpop-backend) python manage.py migrate
```

### Backup do Banco de Dados

```bash
# Backup (via PostgreSQL EXTERNO - adapte conforme seu setup)
pg_dump -h POSTGRES_HOST -U voxpop -d voxpop_prod > backup_$(date +%Y%m%d).sql

# Restore (via PostgreSQL EXTERNO - adapte conforme seu setup)
cat backup_20240220.sql | psql -h POSTGRES_HOST -U voxpop -d voxpop_prod

# NOTA: Se você tiver acesso ao servidor PostgreSQL via SSH, faça:
# ssh postgres-server "pg_dump -U voxpop voxpop_prod" > backup.sql
```

---

## 📈 Monitoramento e Logs

### Ver Logs em Tempo Real

```bash
# Todos os serviços da stack
docker service logs -f voxpop_voxpop-backend
docker service logs -f voxpop_voxpop-celery
docker service logs -f voxpop_voxpop-frontend
```

### Ver Resource Usage

```bash
# Stats de todos os containers
docker stats

# Stats de serviço específico
docker stats $(docker ps -q -f name=voxpop-backend)
```

### Logs no Portainer

1. **Acesse** Portainer → **Containers**
2. **Selecione** o container
3. **Aba** "Logs" para ver em tempo real

---

## 🔍 Troubleshooting

### Problema: Serviço não inicia

```bash
# Verificar status
docker ps -a

# Ver logs
docker logs $(docker ps -q -f name=NOME_DO_SERVICO)

# Ver detalhes do serviço
docker service inspect voxpop_NOME_DO_SERVICO
```

### Problema: Erro 502/503

1. **Verificar se backend está healthy**
   ```bash
   docker inspect --format='{{.State.Health.Status}}' $(docker ps -q -f name=voxpop-backend)
   ```

2. **Verificar logs do backend**
   ```bash
   docker logs $(docker ps -q -f name=voxpop-backend) --tail 100
   ```

3. **Verificar conexão com banco**
   ```bash
   docker exec -it $(docker ps -q -f name=voxpop-backend) python manage.py dbshell
   ```

### Problema: Celery não processa tarefas

```bash
# Verificar se celery worker está rodando
docker exec -it $(docker ps -q -f name=voxpop-celery) celery -A config inspect active

# Verificar filas
docker exec -it $(docker ps -q -f name=voxpop-celery) celery -A config inspect registered_queues

# Reiniciar worker
docker service update --force voxpop_voxpop-celery
```

### Problema: Certificado SSL não funciona

1. **Verificar configuração Traefik**
   - Labels do frontend/backend devem ter: `traefik.http.routers.*.tls.certresolver=letsencryptresolver`

2. **Verificar logs do Traefik**
   ```bash
   docker service logs traefik_traefik --tail 100
   ```

3. **Forçar renovação**
   ```bash
   docker service update --force traefik_traefik
   ```

### Problema: Imagens não atualizam

```bash
# Forçar pull de novas imagens
docker service update --image lpcoutinho/voxpop-backend:latest voxpop_voxpop-backend
docker service update --image lpcoutinho/voxpop-frontend:latest voxpop_voxpop-frontend
```

### Problema: Database connection refused

1. **Verificar variáveis POSTGRES_***
   ```bash
   # Ver variáveis configuradas
   docker service inspect voxpop_voxpop-backend --format '{{.Spec.TaskTemplate.ContainerSpec.Env}}'
   ```

2. **Testar conexão do container para o PostgreSQL externo**
   ```bash
   # Entrar no container backend
   docker exec -it $(docker ps -q -f name=voxpop-backend) bash

   # Testar conexão com PostgreSQL (substitua pelo host real)
   psql -h $POSTGRES_HOST -U voxpop -d voxpop_prod
   ```

3. **Verificar se o banco existe**
   ```bash
   # No servidor PostgreSQL externo
   psql -U postgres -c "\l" | grep voxpop_prod
   ```

4. **Verificar firewall**
   - Certifique-se que o PostgreSQL aceita conexões de fora
   - Verifique `pg_hba.conf` no servidor PostgreSQL
   - Teste com `telnet POSTGRES_HOST 5432` do container

---

## 🔐 Segurança

### Senhas e Chaves

- ✅ Use senhas fortes (mínimo 32 caracteres)
- ✅ Gere SECRET_KEY com comando Python
- ✅ Nunca comite credenciais no Git
- ✅ Use variáveis de ambiente no Portainer
- ✅ Rode backups regularmente do PostgreSQL

### Firewall

```bash
# No UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable

# No CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

---

## 📞 Suporte

Para problemas ou dúvidas:

- 📧 Email: coutinholps@gmail.com
- 📱 WhatsApp: [seu número]
- 📚 Documentação do projeto: [link]

---

## ✅ Checklist de Deploy

Use este checklist antes de cada deploy:

- [ ] Volumes criados (`voxpop_redis_data`, `voxpop_logs`)
- [ ] Banco de dados `voxpop_prod` criado no PostgreSQL EXTERNO
- [ ] Usuário `voxpop` com permissões no PostgreSQL EXTERNO
- [ ] Rede `LaunchNet` existe
- [ ] DNS configurado corretamente
- [ ] Variáveis de ambiente configuradas (incluindo POSTGRES_HOST!)
- [ ] SECRET_KEY gerado e seguro
- [ ] POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD definidos
- [ ] EVOLUTION_API_KEY configurado
- [ ] Imagens buildadas e pushadas
- [ ] Stack deployada no Portainer
- [ ] Todos os serviços com 1/1 replicas
- [ ] Health checks passing
- [ ] Frontend acessível (https://voxpop.tratto.solutions)
- [ ] API respondendo (https://voxpop.tratto.solutions/api/v1/)
- [ ] Conexão com PostgreSQL externo funcionando
- [ ] Celery worker processando tarefas
- [ ] Logs sem erros críticos

Deploy concluído com sucesso! 🎉
