from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.team_member_views import TeamMemberViewSet


router = DefaultRouter()
router.register(r'team-members', TeamMemberViewSet, basename='team-members')


app_name = 'teams'

urlpatterns = [
    path('', include(router.urls)),
]