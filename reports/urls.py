from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'reports'

router = DefaultRouter()
router.register(r'api/dashboards', views.DashboardViewSet, basename='dashboard')
router.register(r'api/widgets', views.WidgetViewSet, basename='widget')

urlpatterns = [
    path('', views.DashboardListView.as_view(), name='dashboard_list'),
    path('create/', views.DashboardCreateView.as_view(), name='dashboard_create'),
    path('<int:pk>/', views.DashboardDetailView.as_view(), name='dashboard_detail'),
    path('<int:pk>/edit/', views.DashboardUpdateView.as_view(), name='dashboard_update'),
    path('<int:dashboard_id>/widgets/create/', views.WidgetCreateView.as_view(), name='widget_create'),
    path('widgets/<int:pk>/edit/', views.WidgetUpdateView.as_view(), name='widget_update'),
    path('widgets/<int:widget_id>/data/', views.WidgetDataView.as_view(), name='widget_data'),
    path('<int:pk>/export/<str:format>/', views.DashboardExportView.as_view(), name='dashboard_export'),
    path('', include(router.urls)),
]