"""
Django settings for production environment.
"""

import os
import logging
from .base import *

# ==========================================
# Segurança Produção
# ==========================================
DEBUG = False
ALLOWED_HOSTS = ['voxpop.tratto.solutions', 'www.voxpop.tratto.solutions']

# SSL/TLS Configuration
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookies Seguros
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# ==========================================
# Database (PostgreSQL)
# ==========================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DATABASE', 'voxpop_prod'),
        'USER': os.getenv('POSTGRES_USERNAME', 'voxpop'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST', 'voxpop_postgres'),
        'PORT': '5432',
        'OPTIONS': {
            'MAX_CONNS': 200,
        }
    }
}

# ==========================================
# Cache e Session (Redis)
# ==========================================
REDIS_URL = os.getenv('REDIS_URL', 'redis://voxpop_redis:6379/0')
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ==========================================
# Celery Configuration
# ==========================================
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://voxpop_redis:6379/1')
CELERY_RESULT_BACKEND = 'redis://voxpop_redis:6379/2'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Sao_Paulo'
CELERY_WORKER_CONCURRENCY = int(os.getenv('CELERY_WORKER_CONCURRENCY', '4'))
CELERY_TASK_ALWAYS_EAGER = False
CELERY_WORKER_LOGLEVEL = 'INFO'
CELERY_BEAT_SCHEDULE = {}
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutos
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutos
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_DISABLE_RATE_LIMITS = False

# ==========================================
# Evolution API (WhatsApp)
# ==========================================
EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL', 'https://evolution.tratto.solutions')
EVOLUTION_API_KEY = os.getenv('EVOLUTION_API_KEY')

# ==========================================
# Email Configuration (Produção)
# ==========================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('SMTP_ADDRESS')
EMAIL_PORT = int(os.getenv('SMTP_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('SMTP_USERNAME')
EMAIL_HOST_PASSWORD = os.getenv('SMTP_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('MAILER_SENDER_EMAIL')
SERVER_EMAIL = os.getenv('MAILER_SENDER_EMAIL')

# ==========================================
# Frontend Configuration
# ==========================================
FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://voxpop.tratto.solutions')
CORS_ALLOWED_ORIGINS = [
    'https://voxpop.tratto.solutions',
    'https://www.voxpop.tratto.solutions',
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False

# ==========================================
# File Upload Configuration
# ==========================================
STATIC_URL = '/static/'
STATIC_ROOT = '/app/static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = '/app/media/'

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# ==========================================
# Logging Configuration
# ==========================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/voxpop.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': os.getenv('LOG_LEVEL', 'INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# ==========================================
# Multi-tenant Settings
# ==========================================
PUBLIC_SCHEMA_URLCONF = 'config.urls_public'
TENANT_SCHEMA_URLCONF = 'config.urls'

# ==========================================
# Performance Settings
# ==========================================
CONN_MAX_AGE = 60
USE_TZ = True
TIME_ZONE = 'America/Sao_Paulo'
LANGUAGE_CODE = 'pt-br'
USE_I18N = True
USE_L10N = True

# ==========================================
# Security Settings Adicionais
# ==========================================
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# ==========================================
# Global Settings
# ==========================================
ENVIRONMENT = 'production'
NODE_ENV = 'production'
RAILS_ENV = 'production'  # Para compatibilidade com o padrão do compose
INSTALLATION_ENV = 'docker'
RAILS_LOG_TO_STDOUT = True
