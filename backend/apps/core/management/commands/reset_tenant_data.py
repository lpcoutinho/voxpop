"""
Management command to reset all tenant data while preserving users.

Usage:
    python manage.py reset_tenant_data <tenant_slug> [--keep-tags]

This truncates all tables in the tenant's schema (supporters, campaigns,
messages, etc.) while preserving the public schema (users, memberships, tenants).
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django_tenants.utils import schema_context
from django.apps import apps


TENANT_APPS = [
    'supporters',
    'campaigns',
    'messaging',
    'whatsapp',
    'dashboard',
]


class Command(BaseCommand):
    help = 'Remove todos os dados de um tenant preservando usuários e membros'

    def add_arguments(self, parser):
        parser.add_argument(
            'tenant_slug',
            type=str,
            help='Slug do tenant a ser limpo',
        )
        parser.add_argument(
            '--keep-tags',
            action='store_true',
            help='Preserva as tags do tenant',
        )

    def handle(self, *args, **options):
        from tenants.models import Tenant

        try:
            tenant = Tenant.objects.get(slug=options['tenant_slug'])
        except Tenant.DoesNotExist:
            raise CommandError(
                f'Tenant com slug "{options["tenant_slug"]}" não encontrado'
            )

        self.stdout.write(
            f'Limpando dados do tenant "{tenant.name}" (schema: {tenant.schema_name})...'
        )

        apps_to_clear = TENANT_APPS.copy()
        if options['keep_tags']:
            apps_to_clear.remove('supporters')
            apps_to_clear.append('_keep_tags')

        deleted_total = 0

        with schema_context(tenant.schema_name):
            for model in apps.get_models():
                app_label = model._meta.app_label

                if app_label not in apps_to_clear:
                    continue

                if options['keep_tags'] and app_label == 'supporters':
                    model_name = model.__name__.lower()
                    if model_name == 'tag':
                        continue

                deleted, _ = model.objects.all().delete()
                if deleted:
                    self.stdout.write(
                        f'  {model._meta.verbose_name_plural or model.__name__}: '
                        f'{deleted} deletados'
                    )
                    deleted_total += deleted

        self.stdout.write(self.style.SUCCESS(
            f'Pronto! {deleted_total} registros deletados do tenant "{tenant.name}".\n'
            f'Usuários, membros e configurações do tenant foram preservados.'
        ))
