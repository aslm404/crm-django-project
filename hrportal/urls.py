"""
URL configuration for hrportal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from hrportal.views import MaintenanceView
from team.views import CustomLogoutView, DashboardView, ClientRegistrationView  


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Maintenance
    path('maintenance/', MaintenanceView.as_view(), name='maintenance'),
    
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', ClientRegistrationView.as_view(), name='register'),
    
    # Password Reset
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='auth/password_reset.html'), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'), 
         name='password_reset_complete'),
    
    # Apps
    path('', DashboardView.as_view(), name='home'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('team/', include('team.urls')),
    path('projects/', include('projects.urls')),
    path('tasks/', include('tasks.urls')),
    path('clients/', include('clients.urls')),
    path('invoices/', include('invoices.urls')),
    path('support/', include('support.urls')),
    path('reports/', include('reports.urls')),
    path('chat/', include('chat.urls')),
    path('paypal/', include('paypal.standard.ipn.urls')),
    
    # API
    path('api/', include('team.api.urls')),
    path('api/projects/', include('projects.api.urls')),
    path('api/tasks/', include('tasks.api.urls')),
    path('api/invoices/', include('invoices.api.urls')),
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)