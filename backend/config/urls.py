"""
URL configuration for VoxPop project (tenant schemas).
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    # API v1
    path('api/v1/', include([
        path('auth/', include('apps.accounts.api.urls')),
        path('tenants/', include('apps.tenants.api.urls')),
        path('supporters/', include('apps.supporters.api.urls')),
        path('campaigns/', include('apps.campaigns.api.urls')),
        path('messages/', include('apps.messaging.api.urls')),
        path('whatsapp/', include('apps.whatsapp.api.urls')),
        path('teams/', include('apps.teams.api.urls')),
        path('dashboard/', include('apps.dashboard.api.urls')),
    ])),
]
