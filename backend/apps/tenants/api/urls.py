from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PlanListView,
    TenantCreateView,
    AdminPlanViewSet,
    AdminOrganizationViewSet,
    AdminUserViewSet,
    AdminStatsView,
)
from .views.member_views import MemberViewSet

app_name = 'tenants'

# Admin router
admin_router = DefaultRouter()
admin_router.register(r'organizations', AdminOrganizationViewSet, basename='admin-organization')
admin_router.register(r'plans', AdminPlanViewSet, basename='admin-plan')
admin_router.register(r'users', AdminUserViewSet, basename='admin-user')

# Tenant router (for current tenant operations)
router = DefaultRouter()
router.register(r'members', MemberViewSet, basename='tenant-members')

urlpatterns = [
    # Public endpoints
    path('plans/', PlanListView.as_view(), name='plan-list'),
    path('register/', TenantCreateView.as_view(), name='tenant-register'),

    # Tenant endpoints
    path('', include(router.urls)),

    # Admin endpoints (superuser only)
    path('admin/', include(admin_router.urls)),
    path('admin/stats/', AdminStatsView.as_view(), name='admin-stats'),
]
