from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.tenants.models import Client, Domain, Plan, TenantMembership
from apps.accounts.models import User

class Command(BaseCommand):
    help = 'Creates test users and tenants (Superadmin, Tenant Admin, Tenant User)'

    def handle(self, *args, **options):
        self.stdout.write('Creating test data...')

        try:
            with transaction.atomic():
                # 1. Create Plan
                plan, created = Plan.objects.get_or_create(
                    slug='free',
                    defaults={
                        'name': 'Free Tier',
                        'max_supporters': 100,
                        'max_messages_month': 1000,
                        'max_campaigns': 1,
                        'max_whatsapp_sessions': 1,
                        'price': 0.00
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Plan "{plan.name}" created.'))
                else:
                    self.stdout.write(f'Plan "{plan.name}" already exists.')

                # 2. Create Public Tenant (if not exists)
                # We check for a tenant with schema_name='public'
                public_client = Client.objects.filter(schema_name='public').first()
                if not public_client:
                    self.stdout.write('Creating Public Tenant...')
                    public_client = Client.objects.create(
                        schema_name='public',
                        name='Public Tenant',
                        slug='public',
                        plan=plan
                    )
                    # Create Domain for Public Tenant
                    if not Domain.objects.filter(domain='localhost').exists():
                        Domain.objects.create(
                            domain='localhost',
                            tenant=public_client,
                            is_primary=True
                        )
                    self.stdout.write(self.style.SUCCESS('Public Tenant created.'))
                else:
                    self.stdout.write('Public Tenant already exists.')

                # 3. Create Demo Tenant
                demo_client = Client.objects.filter(schema_name='demo').first()
                if not demo_client:
                    self.stdout.write('Creating Demo Tenant (this triggers schema creation, please wait)...')
                    demo_client = Client.objects.create(
                        schema_name='demo',
                        name='Demo Organization',
                        slug='demo',
                        plan=plan
                    )
                    # Create Domain for Demo Tenant
                    # We use a subdomain or a different port/domain depending on setup.
                    # Assuming 'demo.localhost' for now.
                    if not Domain.objects.filter(domain='demo.localhost').exists():
                        Domain.objects.create(
                            domain='demo.localhost',
                            tenant=demo_client,
                            is_primary=True
                        )
                    self.stdout.write(self.style.SUCCESS('Demo Tenant created.'))
                else:
                    self.stdout.write('Demo Tenant already exists.')

                # 4. Create Users
                User = get_user_model()

                # Superuser
                superuser, created = User.objects.get_or_create(
                    email='superuser@voxpop.com',
                    defaults={
                        'first_name': 'Super',
                        'last_name': 'Admin',
                        'is_staff': True,
                        'is_superuser': True,
                        'is_verified': True
                    }
                )
                superuser.set_password('voxpop123')
                superuser.save()
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Superuser "{superuser.email}" created.'))
                else:
                    self.stdout.write(f'Superuser "{superuser.email}" updated (password reset).')

                # Admin User (Tenant Admin)
                admin_user, created = User.objects.get_or_create(
                    email='admin@voxpop.com',
                    defaults={
                        'first_name': 'Tenant',
                        'last_name': 'Admin',
                        'is_verified': True
                    }
                )
                admin_user.set_password('voxpop123')
                admin_user.save()
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Admin User "{admin_user.email}" created.'))
                else:
                    self.stdout.write(f'Admin User "{admin_user.email}" updated (password reset).')

                # Common User (Tenant Viewer)
                common_user, created = User.objects.get_or_create(
                    email='user@voxpop.com',
                    defaults={
                        'first_name': 'Common',
                        'last_name': 'User',
                        'is_verified': True
                    }
                )
                common_user.set_password('voxpop123')
                common_user.save()
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Common User "{common_user.email}" created.'))
                else:
                    self.stdout.write(f'Common User "{common_user.email}" updated (password reset).')

                # 5. Assign Memberships
                # Admin -> Demo Tenant (Admin)
                if not TenantMembership.objects.filter(user=admin_user, tenant=demo_client).exists():
                    TenantMembership.objects.create(
                        user=admin_user,
                        tenant=demo_client,
                        role=TenantMembership.Role.ADMIN
                    )
                    self.stdout.write(self.style.SUCCESS(f'Assigned Admin role to {admin_user.email} in Demo Tenant.'))

                # User -> Demo Tenant (Viewer)
                if not TenantMembership.objects.filter(user=common_user, tenant=demo_client).exists():
                    TenantMembership.objects.create(
                        user=common_user,
                        tenant=demo_client,
                        role=TenantMembership.Role.VIEWER
                    )
                    self.stdout.write(self.style.SUCCESS(f'Assigned Viewer role to {common_user.email} in Demo Tenant.'))
                
                # Set current_tenant for easier login
                admin_user.current_tenant = demo_client
                admin_user.save()
                common_user.current_tenant = demo_client
                common_user.save()
                
                # Superuser doesn't necessarily need a current_tenant, but setting it doesn't hurt
                superuser.current_tenant = demo_client 
                superuser.save()

            self.stdout.write(self.style.SUCCESS('All test data checked/created successfully!'))
            self.stdout.write('---------------------------------------------------------')
            self.stdout.write('Credentials (password: voxpop123):')
            self.stdout.write('  Superadmin:   superuser@voxpop.com')
            self.stdout.write('  Tenant Admin: admin@voxpop.com')
            self.stdout.write('  Tenant User:  user@voxpop.com')
            self.stdout.write('---------------------------------------------------------')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating test data: {str(e)}'))
            raise e
