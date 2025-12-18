from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from Aplicaciones.views import login_view, logout_view 

urlpatterns = [
    
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # LOGOUT
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('', include('Aplicaciones.urls')),
    # Aquí incluyes tu app
]