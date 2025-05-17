from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'support'

router = DefaultRouter()
router.register(r'api/tickets', views.SupportTicketViewSet, basename='ticket')
router.register(r'api/comments', views.TicketCommentViewSet, basename='comment')
router.register(r'api/categories', views.TicketCategoryViewSet, basename='category')

urlpatterns = [
    path('', views.TicketListView.as_view(), name='ticket_list'),
    path('create/', views.TicketCreateView.as_view(), name='ticket_create'),
    path('<int:pk>/', views.TicketDetailView.as_view(), name='ticket_detail'),
    path('<int:pk>/update-status/', views.TicketStatusUpdateView.as_view(), name='ticket_status_update'),
    path('<int:pk>/add-comment/', views.AddCommentView.as_view(), name='add_comment'),
    path('categories/', views.TicketCategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.TicketCategoryCreateView.as_view(), name='category_create'),
    path('', include(router.urls)),
]