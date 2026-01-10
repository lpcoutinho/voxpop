from django.contrib import admin
from django_tenants.admin import TenantAdminMixin

from .models import Client, Domain, Plan, TenantMembership


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'max_supporters', 'max_messages_month', 'is_active']
    list_filter = ['is_active', 'is_public']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['price']


class DomainInline(admin.TabularInline):
    model = Domain
    extra = 1


class MembershipInline(admin.TabularInline):
    model = TenantMembership
    extra = 1
    raw_id_fields = ['user']


@admin.register(Client)
class ClientAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'schema_name', 'plan', 'is_active', 'created_at']
    list_filter = ['is_active', 'plan', 'created_at']
    search_fields = ['name', 'slug', 'document', 'schema_name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['schema_name', 'created_at', 'updated_at']
    inlines = [DomainInline, MembershipInline]
    fieldsets = [
        (None, {
            'fields': ['name', 'slug', 'document', 'plan']
        }),
        ('Contato', {
            'fields': ['email', 'phone']
        }),
        ('Configurações', {
            'fields': ['is_active', 'settings'],
            'classes': ['collapse']
        }),
        ('Informações do Sistema', {
            'fields': ['schema_name', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'tenant', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['domain', 'tenant__name']
    raw_id_fields = ['tenant']


@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'tenant']
    search_fields = ['user__email', 'tenant__name']
    raw_id_fields = ['user', 'tenant']
