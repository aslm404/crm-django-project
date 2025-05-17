from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

app_name = 'tasks'

router = DefaultRouter()
router.register(r'api/tasks', views.TaskViewSet, basename='task')
router.register(r'api/time-entries', views.TimeEntryViewSet, basename='timeentry')
router.register(r'api/recurring-tasks', views.RecurringTaskViewSet, basename='recurringtask')

urlpatterns = [
    path('', views.TaskListView.as_view(), name='list'),
    path('create/', views.TaskCreateView.as_view(), name='create'),
    path('<int:pk>/', views.TaskDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.TaskUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.TaskDeleteView.as_view(), name='delete'),
    path('<int:pk>/timer/', views.TimerActionView.as_view(), name='timer_action'),
    path('time-entries/', views.TimeEntryListView.as_view(), name='time_entry_list'),
    path('time-entries/create/', views.TimeEntryCreateView.as_view(), name='time_entry_create'),
    path('recurring/', views.RecurringTaskListView.as_view(), name='recurring_task_list'),
    path('recurring/create/', views.RecurringTaskCreateView.as_view(), name='recurring_task_create'),
    path('recurring/<int:pk>/edit/', views.RecurringTaskUpdateView.as_view(), name='recurring_task_update'),
    path('', include(router.urls)),
]