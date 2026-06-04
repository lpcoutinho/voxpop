#!/bin/bash

# =============================================================================
# BUILD IMAGES SCRIPT - VoxPop
# =============================================================================
# Script para construir e fazer push das imagens Docker do VoxPop
#
# Uso:
#   chmod +x build-images.sh
#   ./build-images.sh
#
# =============================================================================

set -e  # Para o script se houver erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variáveis
BACKEND_IMAGE="lpcoutinho/voxpop-backend:latest"
FRONTEND_IMAGE="lpcoutinho/voxpop-frontend:latest"
DOCKER_REGISTRY="docker.io"

# Funções de log
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Função para verificar se Docker está rodando
check_docker() {
    log_info "Verificando se Docker está rodando..."
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker não está rodando. Inicie o Docker primeiro."
        exit 1
    fi
    log_success "Docker está rodando"
}

# Função para verificar login no Docker Hub
check_docker_login() {
    log_info "Verificando login no Docker Hub..."

    # Tenta verificar se está logado
    if ! docker info | grep -q "Username"; then
        log_warning "Você não está logado no Docker Hub."
        log_info "Execute: docker login"
        read -p "Deseja fazer login agora? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker login
        else
            log_error "Login necessário para fazer push das imagens."
            exit 1
        fi
    fi
    log_success "Login no Docker Hub verificado"
}

# Função para build da imagem backend
build_backend() {
    log_info "=========================================="
    log_info "Iniciando build da imagem BACKEND..."
    log_info "=========================================="

    cd backend

    log_info "Buildando: $BACKEND_IMAGE"
    docker build -f Dockerfile.prod -t "$BACKEND_IMAGE" .

    if [ $? -eq 0 ]; then
        log_success "Build do backend concluído com sucesso!"
    else
        log_error "Erro ao buildar imagem do backend."
        exit 1
    fi

    cd ..
}

# Função para build da imagem frontend
build_frontend() {
    log_info "=========================================="
    log_info "Iniciando build da imagem FRONTEND..."
    log_info "=========================================="

    cd frontend

    log_info "Buildando: $FRONTEND_IMAGE"
    docker build \
        -f Dockerfile.prod \
        --build-arg VITE_API_URL="https://voxpopapi.tratto.solutions/api/v1" \
        -t "$FRONTEND_IMAGE" .

    if [ $? -eq 0 ]; then
        log_success "Build do frontend concluído com sucesso!"
    else
        log_error "Erro ao buildar imagem do frontend."
        exit 1
    fi

    cd ..
}

# Função para push da imagem backend
push_backend() {
    log_info "=========================================="
    log_info "Fazendo push da imagem BACKEND..."
    log_info "=========================================="

    log_info "Push: $BACKEND_IMAGE"
    docker push "$BACKEND_IMAGE"

    if [ $? -eq 0 ]; then
        log_success "Push do backend concluído com sucesso!"
    else
        log_error "Erro ao fazer push da imagem do backend."
        exit 1
    fi
}

# Função para push da imagem frontend
push_frontend() {
    log_info "=========================================="
    log_info "Fazendo push da imagem FRONTEND..."
    log_info "=========================================="

    log_info "Push: $FRONTEND_IMAGE"
    docker push "$FRONTEND_IMAGE"

    if [ $? -eq 0 ]; then
        log_success "Push do frontend concluído com sucesso!"
    else
        log_error "Erro ao fazer push da imagem do frontend."
        exit 1
    fi
}

# Função para mostrar informações das imagens
show_images_info() {
    log_info "=========================================="
    log_info "Informações das Imagens"
    log_info "=========================================="

    echo ""
    docker images | grep voxpop

    echo ""
    log_info "Tamanhos:"
    docker images voxpop-backend:latest --format "Backend: {{.Size}}"
    docker images voxpop-frontend:latest --format "Frontend: {{.Size}}"
}

# Função principal
main() {
    clear

    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║          VOXPOP - DOCKER IMAGES BUILD SCRIPT              ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    # Verificações
    check_docker
    check_docker_login

    echo ""
    log_info "Este script irá:"
    echo "   1. Buildar a imagem backend (Django + Gunicorn)"
    echo "   2. Buildar a imagem frontend (React + Nginx)"
    echo "   3. Fazer push das imagens para o Docker Hub"
    echo ""
    read -p "Deseja continuar? (y/n) " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warning "Operação cancelada pelo usuário."
        exit 0
    fi

    # Executa builds
    build_backend
    build_frontend

    echo ""
    log_warning "Deseja fazer push das imagens para o Docker Hub?"
    read -p " Isso pode levar vários minutos dependendo da velocidade da internet. (y/n) " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        push_backend
        push_frontend
    else
        log_warning "Push cancelado. Imagens foram apenas buildadas localmente."
        log_info "Para fazer push manualmente:"
        echo "   docker push $BACKEND_IMAGE"
        echo "   docker push $FRONTEND_IMAGE"
    fi

    # Mostra informações finais
    echo ""
    show_images_info

    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║              BUILD CONCLUÍDO COM SUCESSO! 🎉               ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    log_success "Próximos passos:"
    echo "   1. Acesse o Portainer: https://portainer.seudominio.com"
    echo "   2. Vá em Stacks → Add stack"
    echo "   3. Cole o conteúdo de docker-compose.stack.yml"
    echo "   4. Configure as variáveis de ambiente"
    echo "   5. Clique em Deploy"
    echo ""
    log_info "Ou via SSH:"
    echo "   docker stack deploy -c docker-compose.stack.yml voxpop"
    echo ""
}

# Executa script
main
