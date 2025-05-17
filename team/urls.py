from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

app_name = 'team'

router = DefaultRouter()
router.register(r'api/users', views.UserViewSet, basename='user')
router.register(r'api/roles', views.RoleViewSet, basename='role')

urlpatterns = [
    # Authentication
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('register/', views.ClientRegistrationView.as_view(), name='register'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),

    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),

    # Team Management
    path('list/', views.TeamListView.as_view(), name='team_list'),
    path('create/', views.TeamCreateView.as_view(), name='team_create'),
    path('<int:pk>/', views.TeamDetailView.as_view(), name='team_detail'),
    path('<int:pk>/edit/', views.TeamUpdateView.as_view(), name='team_update'),

    # Roles
    path('roles/', views.RoleListView.as_view(), name='role_list'),
    path('roles/create/', views.RoleCreateView.as_view(), name='role_create'),
    path('roles/<int:pk>/edit/', views.RoleUpdateView.as_view(), name='role_update'),

    # API
    path('', include(router.urls)),
]