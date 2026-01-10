from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.whatsapp.api.views import WhatsAppSessionViewSet, WebhookView

app_name = 'whatsapp'

router = DefaultRouter()
router.register(r'sessions', WhatsAppSessionViewSet, basename='session')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/<str:instance_name>/', WebhookView.as_view(), name='webhook'),
]
