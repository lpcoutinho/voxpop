from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.supporters.api.views import (
    SupporterViewSet,
    TagViewSet,
    SegmentViewSet,
    ImportViewSet,
)

app_name = 'supporters'

router = DefaultRouter()
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'segments', SegmentViewSet, basename='segment')
router.register(r'import', ImportViewSet, basename='import')
router.register(r'', SupporterViewSet, basename='supporter')

urlpatterns = [
    path('', include(router.urls)),
]
