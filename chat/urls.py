from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'chat'

router = DefaultRouter()
router.register(r'api/conversations', views.ConversationViewSet, basename='conversation')
router.register(r'api/messages', views.MessageViewSet, basename='message')

urlpatterns = [
    path('', views.ChatHomeView.as_view(), name='home'),
    path('conversations/', views.ConversationListView.as_view(), name='conversation_list'),
    path('conversations/create/', views.ConversationCreateView.as_view(), name='conversation_create'),
    path('conversations/<int:pk>/', views.ConversationDetailView.as_view(), name='conversation_detail'),
    path('', include(router.urls)),
]