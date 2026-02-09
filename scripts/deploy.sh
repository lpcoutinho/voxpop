#!/bin/bash
set -e

echo "🚀 Deploy VoxPop Produção via Portainer"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Verificação de pré-requisitos
echo -e "${YELLOW}📋 Verificando pré-requisitos...${NC}"

# Verificar se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker não está rodando. Inicie o Docker primeiro.${NC}"
    exit 1
fi

# Verificar se arquivo .env.production existe
if [ ! -f ".env.production" ]; then
    echo -e "${RED}❌ Arquivo .env.production não encontrado. Crie o arquivo com as credenciais.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Pré-requisitos OK${NC}"

# Build das imagens
echo -e "${YELLOW}🏗️ Buildando imagens...${NC}"
./scripts/build-images.sh

# Criar volumes externos se não existirem
echo -e "${YELLOW}📦 Verificando volumes externos...${NC}"
docker volume create voxpop_postgres_data || true
docker volume create voxpop_redis_data || true
docker volume create voxpop_static || true
docker volume create voxpop_media || true

echo -e "${GREEN}✅ Volumes verificados${NC}"

# Verificar rede LaunchNet
echo -e "${YELLOW}🌐 Verificando rede...${NC}"
docker network create LaunchNet || true
echo -e "${GREEN}✅ Rede verificada${NC}"

# Deploy com docker-compose
echo -e "${YELLOW}🚀 Iniciando deploy...${NC}"
docker stack deploy -c docker-compose.production.yml voxpop

if [ $? -eq 0 ]; then
    echo -e "${GREEN}🎉 Deploy iniciado com sucesso!${NC}"
    echo -e "${YELLOW}📍 Acesse: https://voxpop.tratto.solutions${NC}"
    echo -e "${YELLOW}📊 Portainer: Configure no painel do Portainer${NC}"
    
    # Aguardar serviços iniciarem
    echo -e "${YELLOW}⏳ Aguardando serviços iniciarem...${NC}"
    sleep 30
    
    # Verificar status
    docker stack services voxpop
else
    echo -e "${RED}❌ Erro no deploy${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Deploy concluído!${NC}"