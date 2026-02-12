from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.whatsapp.api.views.session_views import WhatsAppSessionViewSet
from apps.whatsapp.api.views.webhook_views import WebhookView

app_name = 'whatsapp'

router = DefaultRouter()
router.register(r'sessions', WhatsAppSessionViewSet, basename='session')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/<str:instance_name>/', WebhookView.as_view(), name='webhook'),
]
