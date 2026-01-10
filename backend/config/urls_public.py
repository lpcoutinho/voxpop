"""
URL configuration for VoxPop project (public schema).
URLs accessible in the public domain, outside of tenant context.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    # Public API (tenant registration, etc)
    path('api/v1/', include([
        path('tenants/', include('apps.tenants.api.urls')),
        path('auth/', include('apps.accounts.api.urls')),
    ])),
]
