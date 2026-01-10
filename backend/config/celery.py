"""
Celery configuration for VoxPop project.
Uses tenant-schemas-celery for multi-tenant support.
"""
import os

from celery import Celery
from celery.signals import beat_init
from tenant_schemas_celery.app import CeleryApp as TenantAwareCeleryApp

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

app = TenantAwareCeleryApp('voxpop')

# Load settings from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()


@beat_init.connect
def on_beat_init(**kwargs):
    """
    Ensure celery beat uses the public schema.
    django_celery_beat tables are in the public schema.
    """
    from django.db import connection
    connection.set_schema_to_public()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to test Celery is working."""
    print(f'Request: {self.request!r}')
