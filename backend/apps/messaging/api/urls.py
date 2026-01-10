from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.messaging.api.views import MessageTemplateViewSet

app_name = 'messaging'

router = DefaultRouter()
router.register(r'templates', MessageTemplateViewSet, basename='template')

urlpatterns = [
    path('', include(router.urls)),
]
