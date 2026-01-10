from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import MeView, UserTenantsView, ChangePasswordView

app_name = 'accounts'

urlpatterns = [
    # JWT Auth
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # User
    path('me/', MeView.as_view(), name='me'),
    path('me/tenants/', UserTenantsView.as_view(), name='user-tenants'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]
