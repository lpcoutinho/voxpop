#!/bin/bash
set -e

echo "=========================================="
echo "VoxPop - Iniciando..."
echo "=========================================="

# Aguardar banco de dados
if [ -n "$DB_HOST" ]; then
    echo "Aguardando PostgreSQL em ${DB_HOST}:${DB_PORT:-5432}..."
    while ! pg_isready -h "${DB_HOST}" -p "${DB_PORT:-5432}" -U "${DB_USER:-voxpop}" -q 2>/dev/null; do
        echo "  PostgreSQL nao disponivel, aguardando..."
        sleep 2
    done
    echo "PostgreSQL disponivel!"
fi

# Rodar migracoes (se solicitado)
if [ "$RUN_MIGRATIONS" = "1" ] || [ "$RUN_MIGRATIONS" = "true" ]; then
    echo ""
    echo "Executando migracoes..."
    python manage.py migrate --noinput
    echo "Migracoes concluidas!"
fi

# Criar superusuario (se solicitado e nao existir)
if [ "$CREATE_SUPERUSER" = "1" ] || [ "$CREATE_SUPERUSER" = "true" ]; then
    echo ""
    echo "Verificando superusuario..."
    python manage.py shell -c "
from apps.accounts.models import User
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        email='${DJANGO_SUPERUSER_EMAIL:-admin@voxpop.com.br}',
        password='${DJANGO_SUPERUSER_PASSWORD:-admin123}'
    )
    print('Superusuario criado!')
else:
    print('Superusuario ja existe.')
"
fi

# Coletar arquivos estaticos (producao)
if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.production" ]; then
    echo ""
    echo "Coletando arquivos estaticos..."
    python manage.py collectstatic --noinput
    echo "Arquivos estaticos coletados!"
fi

echo ""
echo "=========================================="
echo "Iniciando aplicacao..."
echo "=========================================="

# Executar comando passado
exec "$@"
