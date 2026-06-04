#!/bin/bash

# Script para iniciar toda a stack de desenvolvimento

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Diretório do projeto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Iniciando VoxPop..."
echo ""

# Inicia backend
echo "📦 Iniciando backend..."
cd "$PROJECT_DIR/backend" && docker compose up -d

echo ""
echo -e "${GREEN}✓ Backend iniciado!${NC}"
echo ""

# Inicia frontend em background
echo "🎨 Iniciando frontend..."
cd "$PROJECT_DIR/frontend" && npm run dev &
FRONTEND_PID=$!

echo ""
sleep 3

echo -e "${GREEN}✓ Frontend iniciado!${NC}"
echo ""
echo "========================================"
echo -e "${GREEN}✓ Stack de desenvolvimento iniciada!${NC}"
echo "========================================"
echo ""
echo "Servicos disponiveis:"
echo "  - Backend:  http://localhost:8001"
echo "  - Frontend: http://localhost:8080"
echo ""
echo "Pressione Ctrl+C para parar tudo..."
echo ""

# Função para limpar ao sair
cleanup() {
    echo ""
    echo "🛑 Parando servicos..."
    kill $FRONTEND_PID 2>/dev/null
    cd "$PROJECT_DIR/backend" && docker compose down
    echo -e "${GREEN}✓ Servicos parados!${NC}"
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT SIGTERM

# Mantém o script rodando
wait $FRONTEND_PID
