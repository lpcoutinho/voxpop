"""
Management command to create system tags for all tenants.
"""
from django.core.management.base import BaseCommand
from django.db import connection

from apps.tenants.models import Client
from apps.supporters.models import Tag


class Command(BaseCommand):
    help = 'Create system tags (Lead, Apoiador, Blacklist) for all tenants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            help='Specific tenant slug to create tags for (optional)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating'
        )

    def handle(self, *args, **options):
        tenant_slug = options.get('tenant')
        dry_run = options.get('dry_run', False)

        if tenant_slug:
            tenants = Client.objects.filter(slug=tenant_slug)
            if not tenants.exists():
                self.stderr.write(
                    self.style.ERROR(f'Tenant "{tenant_slug}" not found.')
                )
                return
        else:
            # Exclude public schema - it doesn't have supporters tables
            tenants = Client.objects.filter(is_active=True).exclude(schema_name='public')

        total_created = 0

        for tenant in tenants:
            self.stdout.write(f'\nProcessing tenant: {tenant.name} ({tenant.schema_name})')

            # Switch to tenant schema
            connection.set_tenant(tenant)

            if dry_run:
                self.stdout.write(self.style.WARNING('  [DRY RUN] Would create:'))
                for slug, data in Tag.SYSTEM_TAGS.items():
                    existing = Tag.objects.filter(slug=slug).exists()
                    status = 'EXISTS' if existing else 'WOULD CREATE'
                    self.stdout.write(f"    - {data['name']} ({slug}): {status}")
            else:
                created_tags = Tag.create_system_tags()
                total_created += len(created_tags)

                if created_tags:
                    self.stdout.write(self.style.SUCCESS(
                        f'  Created {len(created_tags)} tag(s): '
                        f'{", ".join(t.name for t in created_tags)}'
                    ))
                else:
                    self.stdout.write('  All system tags already exist.')

        # Reset to public schema
        connection.set_schema_to_public()

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] No changes were made.'))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'\nDone! Created {total_created} system tag(s) across {tenants.count()} tenant(s).'
            ))
