from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'clients'

router = DefaultRouter()
router.register(r'api/clients', views.ClientViewSet, basename='client')
router.register(r'api/client-notes', views.ClientNoteViewSet, basename='client-note')
router.register(r'api/client-files', views.ClientFileViewSet, basename='client-file')

urlpatterns = [
    path('', views.ClientListView.as_view(), name='list'),
    path('create/', views.ClientCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ClientDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ClientUpdateView.as_view(), name='update'),
    path('<int:pk>/portal/', views.ClientPortalView.as_view(), name='portal'),
    path('<int:client_pk>/notes/create/', views.ClientNoteCreateView.as_view(), name='note_create'),
    path('notes/<int:pk>/edit/', views.ClientNoteUpdateView.as_view(), name='note_update'),
    path('<int:client_pk>/files/upload/', views.ClientFileUploadView.as_view(), name='file_upload'),
] + router.urls