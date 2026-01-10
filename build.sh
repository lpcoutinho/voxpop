#!/bin/bash
# ==========================================
# VoxPop - Script de Build
# ==========================================
set -e

# Configuracoes
IMAGE_NAME="${DOCKER_REGISTRY:-lpcoutinho}/voxpop"
VERSION=$(cat VERSION 2>/dev/null || echo "latest")
FULL_IMAGE="${IMAGE_NAME}:${VERSION}"
TAR_FILE="voxpop_${VERSION}.tar"

echo "=========================================="
echo "VoxPop - Build da Imagem Docker"
echo "=========================================="
echo ""
echo "Imagem: ${FULL_IMAGE}"
echo "Versao: ${VERSION}"
echo ""

# Verificar se Dockerfile existe
if [ ! -f "Dockerfile" ]; then
    echo "Erro: Dockerfile nao encontrado"
    exit 1
fi

# Build
echo "Iniciando build..."
echo ""

docker build \
    --tag "${FULL_IMAGE}" \
    --tag "${IMAGE_NAME}:latest" \
    --build-arg VERSION="${VERSION}" \
    --progress=plain \
    .

if [ $? -eq 0 ]; then
    echo ""
    echo "Build concluido com sucesso!"
    echo ""

    # Mostrar info da imagem
    echo "Informacoes da imagem:"
    docker images "${IMAGE_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    echo ""

    # Salvar em TAR se solicitado
    if [[ "$1" == "--save-tar" ]] || [[ "$2" == "--save-tar" ]]; then
        echo "Salvando imagem em arquivo TAR..."
        docker save -o "${TAR_FILE}" "${FULL_IMAGE}"

        if [ $? -eq 0 ]; then
            echo "Imagem salva em: ${TAR_FILE}"
            echo "Tamanho: $(du -h ${TAR_FILE} | cut -f1)"
            echo ""
            echo "Para transferir para o VPS:"
            echo "  scp ${TAR_FILE} usuario@seu-vps:/caminho/"
            echo ""
            echo "No VPS, carregar com:"
            echo "  docker load -i ${TAR_FILE}"
        fi
    fi

    # Push se solicitado
    if [[ "$1" == "--push" ]] || [[ "$2" == "--push" ]]; then
        echo "Enviando para registry..."
        docker push "${FULL_IMAGE}"
        docker push "${IMAGE_NAME}:latest"
        echo "Push concluido!"
    fi

    echo ""
    echo "Proximos passos:"
    echo "  1. Testar localmente:"
    echo "     docker-compose up -d"
    echo ""
    echo "  2. Push para registry:"
    echo "     ./build.sh --push"
    echo ""
    echo "  3. Deploy no Swarm:"
    echo "     docker stack deploy -c docker-stack.yml voxpop"
    echo ""
else
    echo ""
    echo "Erro durante o build!"
    exit 1
fi
