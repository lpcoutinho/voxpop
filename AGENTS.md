# AGENTS.md - VoxPop Development Guide

**Multi-tenant SaaS for political campaign management with WhatsApp integration**

## 🏗️ Project Overview
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **Backend**: Django 5 + DRF + django-tenants (multi-tenant)
- **Database**: PostgreSQL with schema-per-tenant isolation
- **Queue**: Redis + Celery for background tasks
- **WhatsApp**: Evolution API integration
- **Architecture**: SaaS with role-based permissions (Owner/Admin/Operator/Viewer)

## 🚀 Development Environment

### Quick Start (Docker Compose)
```bash
# Copy environment and configure
cp .env.example .env
# Edit .env with your settings

# Start all services
make dev

# Or rebuild if needed
make dev-build
```

### Key Services & Ports
- Frontend: http://localhost:5173 (Vite dev server)
- Backend API: http://localhost:8000 (Django)
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- MailHog (dev email): http://localhost:8025
- WhatsApp API: http://localhost:8080

## 🛠️ Build/Lint/Test Commands

### Frontend (React/TypeScript)
```bash
cd frontend

# Development
npm run dev              # Start Vite dev server with HMR
npm run build            # Production build
npm run build:dev        # Development build
npm run preview          # Preview production build

# Code Quality
npm run lint             # ESLint check
```

### Backend (Django via Makefile)
```bash
# Development Services
make dev                 # Start all services
make dev-build           # Rebuild and start
make down                # Stop all containers

# Database Operations
make migrate             # All migrations (shared + tenants)
make migrate-shared      # Public schema migrations only
make migrate-tenants     # Tenant migrations only
make makemigrations      # Create new migrations
makesuperuser           # Create admin user

# Testing & Code Quality
make test                # Run all pytest tests
make test-cov            # Tests with HTML coverage report
make lint                # Ruff + Black checks
make format              # Format code (Black + Ruff)

# Development Tools
make shell               # Django shell_plus
make bash                # Backend container bash
make logs service=backend # Service-specific logs
```

### Single Test Execution
```bash
# Specific test file
docker compose exec backend pytest apps/supporters/tests/test_views.py

# Specific test method
docker compose exec backend pytest apps/supporters/tests/test_views.py::TestSupporterViewSet::test_list

# With coverage
docker compose exec backend pytest --cov=apps --cov-report=html apps/supporters/tests/
```

## 🎨 Frontend Code Guidelines

### Component Architecture
- **Naming**: PascalCase for components (`SupporterDataTable.tsx`), camelCase for utilities
- **Structure**: Functional components with TypeScript interfaces
- **Pages**: `pages/` directory with "Page" suffix (`SupportersPage.tsx`)
- **Components**: `components/` organized by feature or shared usage

### Import Organization
```typescript
// External libraries first
import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

// Internal modules with @ alias
import { Button } from '@/components/ui/button';
import { api } from '@/services/api';
import { Supporter } from '@/types';
import { cn } from '@/lib/utils';
```

### State Management Patterns
```typescript
// Server state: TanStack Query
const { data, isLoading, error } = useQuery({
  queryKey: ['supporters', page, search],
  queryFn: () => supportersService.list(filters),
});

// Global state: React Context
const { user, tenant, isAuthenticated } = useAuth();

// Form state: React Hook Form + Zod
const { register, handleSubmit, formState: { errors } } = useForm({
  resolver: zodResolver(loginSchema),
});
```

### Error Handling
```typescript
try {
  await supportersService.create(data);
  toast.success('Apoiador criado com sucesso');
  queryClient.invalidateQueries({ queryKey: ['supporters'] });
} catch (error: unknown) {
  const message = error instanceof Error ? error.message : 'Operação falhou';
  toast.error('Erro ao criar apoiador', { description: message });
}
```

### TypeScript Configuration
- Relaxed mode (`noImplicitAny: false`) for rapid development
- Path aliases: `@/*` maps to `src/*`
- Centralized types in `src/types/index.ts`

## 🐍 Backend Code Guidelines

### Model Inheritance Patterns
```python
# Base model with audit fields
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        abstract = True
        ordering = ['-created_at']

# Soft delete for tenant data
class SoftDeleteModel(BaseModel):
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Deletado em')
    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Includes deleted objects
```

### ViewSet Structure
```python
class SupporterViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsTenantMember]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    def get_queryset(self):
        return Supporter.objects.select_related('created_by').prefetch_related('tags')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SupporterListSerializer
        return SupporterDetailSerializer
```

### Multi-Tenant Patterns
```python
# CRITICAL: Always use schema context for tenant operations
with schema_context(tenant.schema_name):
    supporters = Supporter.objects.all()
    count = supporters.count()

# Tenant-aware permissions
class IsTenantMember(BasePermission):
    def has_permission(self, request, view):
        return request.user.tenant_memberships.filter(
            tenant=request.tenant,
            is_active=True
        ).exists()
```

### Service Layer with Transactions
```python
class SupporterService:
    @transaction.atomic
    def create_with_tags(self, supporter_data: dict, tag_ids: list[int]) -> Supporter:
        supporter = Supporter.objects.create(**supporter_data)
        supporter.tags.set(tag_ids)
        return supporter
```

### Portuguese User-Facing Fields
```python
class Supporter(models.Model):
    name = models.CharField(max_length=200, verbose_name='Nome')
    phone = models.CharField(max_length=20, verbose_name='Telefone')
    email = models.EmailField(verbose_name='Email')
    
    class Status(models.TextChoices):
        LEAD = 'lead', 'Potencial'
        SUPPORTER = 'supporter', 'Apoiador'
        BLACKLIST = 'blacklist', 'Bloqueado'
```

## 📐 Code Style & Formatting

### Frontend Configuration
- **Linter**: ESLint with TypeScript support
- **Formatter**: Prettier (standard configuration)
- **Line Length**: Default Prettier settings
- **Rules**: Relaxed TypeScript rules for development speed

### Backend Configuration
- **Linter**: Ruff (fast Python linter)
- **Formatter**: Black (code formatting)
- **Type Checker**: MyPy with Django stubs (strict mode)
- **Line Length**: 100 characters
- **Import Sorting**: Ruff with isort configuration

```toml
# pyproject.toml excerpt
[tool.ruff]
target-version = "py311"
line-length = 100
select = ["E", "W", "F", "I", "B", "C4", "UP", "DJ"]

[tool.mypy]
python_version = "3.11"
strict = true
plugins = ["mypy_django_plugin.main", "mypy_drf_plugin.main"]
```

## 🧪 Testing Patterns

### Backend Testing
```python
# Test configuration in config/settings/test.py
CELERY_TASK_ALWAYS_EAGER = True  # Run tasks synchronously
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}

# Test patterns
class TestSupporterViewSet(APITestCase):
    def setUp(self):
        self.tenant = create_test_tenant()
        self.user = create_test_user(tenant=self.tenant)
        self.client.force_authenticate(user=self.user)
    
    def test_list_supporters(self):
        # Test implementation
        pass
```

### Frontend Testing (Recommended)
- Add Vitest + React Testing Library
- Component testing with `@testing-library/react`
- Service mocking with `msw` or similar

## 🔑 Critical Rules & Gotchas

### Multi-Tenancy Requirements
1. **Migration Order**: ALWAYS run shared migrations first, then tenant migrations
2. **Schema Context**: All tenant operations must use `with schema_context(tenant.schema_name):`
3. **Tenant Resolution**: `X-Tenant` header for development, domain-based for production
4. **User-Tenant Relations**: Users can belong to multiple tenants with different roles

### Permission Hierarchy (Strict Order)
1. `IsSuperAdmin` - Superuser access
2. `IsTenantOwner` - Tenant owner only
3. `IsTenantAdmin` - Owner or admin
4. `CanEditTenant` - Owner, admin, or operator
5. `IsTenantMember` - Any active tenant member

### API Design Standards
- Consistent error responses: `{error: bool, code: string, message: string}`
- Portuguese messages for all user-facing content
- Nested serializers for relationships (avoid shallow responses)
- Action endpoints for state changes (`/start/`, `/pause/`, `/cancel/`)
- Pagination: 20 items per page default

### WhatsApp Integration
- Use Evolution API for all WhatsApp operations
- Message templates for campaign messages
- Queue organization: `messages_high` (urgent), `messages_low` (bulk)
- Webhook handling with proper tenant isolation

### Environment Configuration
- Development: `DEBUG=1`, `CORS_ALLOW_ALL_ORIGINS=True`
- Production: Security headers, restricted origins, HTTPS only
- All secrets via environment variables, never hardcoded

## 📋 Development Workflow

### Feature Development
1. Create tenant-specific migrations if needed
2. Implement backend models/serializers/views
3. Add comprehensive tests
4. Implement frontend components/pages
5. Add error handling and loading states
6. Test across different user roles
7. Verify tenant isolation works correctly

### Common Gotchas
- **Never access tenant data without schema context**
- **Always run migrations in correct order (shared → tenants)**
- **Use Portuguese for all user-facing strings**
- **Test permissions for all user roles**
- **WhatsApp messages require templates, not free text**
- **Email in development goes to MailHog, not real SMTP**

### Debugging Commands
```bash
# Check tenant schemas
docker compose exec db psql -U voxpop -d voxpop_db -c "\dn+"

# Django shell with tenant context
make shell
# Then: from django_tenants.utils import schema_context

# View all celery queues
docker compose exec redis redis-cli keys "*"

# Check tenant-specific data
docker compose exec backend python manage.py shell_plus --schema=tenant_slug
```

Remember: This is a multi-tenant SaaS. **Tenant isolation is the most critical requirement** - always verify your code respects tenant boundaries and uses proper schema contexts.