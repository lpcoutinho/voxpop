#!/bin/bash
set -e

echo "🚀 Buildando imagens VoxPop para produção..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📦 Buildando imagem backend...${NC}"
docker build -t lpcoutinho/voxpop-backend:latest -f backend/Dockerfile.prod ./backend/
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend build concluído${NC}"
else
    echo -e "${RED}❌ Erro no build do backend${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 Buildando imagem frontend...${NC}"
docker build -t lpcoutinho/voxpop-frontend:latest -f frontend/Dockerfile.prod ./frontend/
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Frontend build concluído${NC}"
else
    echo -e "${RED}❌ Erro no build do frontend${NC}"
    exit 1
fi

echo -e "${YELLOW}📤 Enviando imagens para registry...${NC}"
docker push lpcoutinho/voxpop-backend:latest
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend enviado para registry${NC}"
else
    echo -e "${RED}❌ Erro ao enviar backend${NC}"
    exit 1
fi

docker push lpcoutinho/voxpop-frontend:latest
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Frontend enviado para registry${NC}"
else
    echo -e "${RED}❌ Erro ao enviar frontend${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 Build concluído com sucesso!${NC}"
echo -e "${GREEN}🔄 Pronto para deploy no Portainer!${NC}"