# ============================================
# VoxPop - Dockerfile Multi-stage Production
# ============================================

# ============================================
# STAGE 1: Frontend Build
# ============================================
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Instalar dependencias
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --only=production

# Copiar codigo e buildar
COPY frontend/ ./

# Build args para configuracao do frontend
ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build


# ============================================
# STAGE 2: Backend Production
# ============================================
FROM python:3.11-slim AS production

# Variaveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    PORT=8000

WORKDIR /app

# Instalar dependencias do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY backend/requirements/base.txt backend/requirements/production.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/production.txt \
    && rm -rf /tmp/*.txt

# Copiar backend
COPY backend/ /app/

# Copiar frontend build para servir via whitenoise
COPY --from=frontend-builder /frontend/dist /app/frontend-dist

# Copiar entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Criar usuario nao-root
RUN adduser --disabled-password --gecos '' --uid 1000 appuser \
    && mkdir -p /app/staticfiles /app/media \
    && chown -R appuser:appuser /app

# Coletar static files (precisa de SECRET_KEY dummy)
RUN SECRET_KEY=build-placeholder python manage.py collectstatic --noinput || true

USER appuser

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "--worker-class", "gthread", "--worker-tmp-dir", "/dev/shm"]
