from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from Aplicaciones.views import login_view


urlpatterns = [
    # ======================
    # ADMIN
    # ======================
    path('admin/', admin.site.urls),

    # ======================
    # AUTENTICACIÓN (TEMPLATES)
    # ======================
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    # ======================
    # AUTENTICACIÓN API (JWT)
    # ======================
    path('api/login/', TokenObtainPairView.as_view(), name='api_login'),
    path('api/refresh/', TokenRefreshView.as_view(), name='api_refresh'),

    # ======================
    # APLICACIÓN PRINCIPAL
    # ======================
    path('', include('Aplicaciones.urls')),
]
