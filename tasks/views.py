from django.utils import timezone
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, Http404
from django.db.models import Q
from .models import Task, TimeEntry, RecurringTask
from .forms import TaskForm, TimeEntryForm, RecurringTaskForm
from rest_framework import viewsets
from .serializers import TaskSerializer, TimeEntrySerializer, RecurringTaskSerializer
from team.permissions import IsAdminOrReadOnly
from clients.models import Client

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/list.html'
    context_object_name = 'tasks'
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Task.objects.none()
        queryset = Task.objects.select_related('project', 'project__client', 'created_by').prefetch_related('assignees')
        if user.is_superuser:
            return queryset
        elif user.role == 'admin':
            return queryset.filter(created_by=user)
        elif user.role == 'staff' and user.created_by:
            return queryset.filter(created_by=user.created_by)
        elif user.role == 'client':
            try:
                client = Client.objects.get(user=user)
                return queryset.filter(project__client=client)
            except Client.DoesNotExist:
                return queryset.none()
        return queryset.filter(Q(assignees=user) | Q(created_by=user))

class TaskCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/form.html'
    
    def test_func(self):
        return self.request.user.role in ['admin', 'staff']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = self.request.user.role == 'admin'
        return context
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        # Force assignees to be the logged-in admin if role is admin
        if self.request.user.role == 'admin':
            form.instance.assignees.set([self.request.user])
        return response
    
    def get_success_url(self):
        return reverse_lazy('tasks:detail', kwargs={'pk': self.object.pk})

class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'tasks/detail.html'
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Task.objects.none()
        queryset = Task.objects.select_related('project', 'project__client', 'created_by').prefetch_related('assignees')
        if user.is_superuser:
            return queryset
        elif user.role == 'admin':
            return queryset.filter(created_by=user)
        elif user.role == 'staff' and user.created_by:
            return queryset.filter(created_by=user.created_by)
        elif user.role == 'client':
            try:
                client = Client.objects.get(user=user)
                return queryset.filter(project__client=client)
            except Client.DoesNotExist:
                return queryset.none()
        return queryset.filter(Q(assignees=user) | Q(created_by=user))
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        if user.is_superuser or \
           (user.role == 'admin' and obj.created_by == user) or \
           (user.role == 'staff' and user.created_by and obj.created_by == user.created_by) or \
           (user.role == 'client' and hasattr(user, 'client_profile') and obj.project.client == user.client_profile) or \
           (user in obj.assignees.all()) or \
           (obj.created_by == user):
            return obj
        raise Http404("You do not have permission to view this task.")

class TaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/form.html'
    
    def test_func(self):
        return self.request.user.role in ['admin', 'manager'] or self.get_object().created_by == self.request.user
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Task.objects.none()
        if user.is_superuser:
            return Task.objects.all().select_related('project', 'project__client', 'created_by').prefetch_related('assignees')
        elif user.role == 'admin':
            return Task.objects.filter(created_by=user).select_related('project', 'project__client', 'created_by').prefetch_related('assignees')
        elif user.role == 'staff' and user.created_by:
            return Task.objects.filter(created_by=user.created_by).select_related('project', 'project__client', 'created_by').prefetch_related('assignees')
        return Task.objects.filter(created_by=user).select_related('project', 'project__client', 'created_by').prefetch_related('assignees')
    
    def get_success_url(self):
        return reverse_lazy('tasks:detail', kwargs={'pk': self.object.pk})

class TaskDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Task
    template_name = 'tasks/confirm_delete.html'
    success_url = reverse_lazy('tasks:list')
    
    def test_func(self):
        return self.request.user.role == 'admin'
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Task.objects.none()
        if user.is_superuser or user.role == 'admin':
            return Task.objects.filter(created_by=user).select_related('project', 'project__client', 'created_by').prefetch_related('assignees')
        return Task.objects.none()

class TimerActionView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        user = self.request.user
        if user.is_superuser or \
           (user.role == 'admin' and task.created_by == user) or \
           (user.role == 'staff' and user.created_by and task.created_by == user.created_by) or \
           (user in task.assignees.all()) or \
           (task.created_by == user):
            running_entry = TimeEntry.objects.filter(
                user=request.user, 
                end_time__isnull=True
            ).first()
            
            if running_entry:
                running_entry.end_time = timezone.now()
                running_entry.save()
                action = 'stopped'
            else:
                TimeEntry.objects.create(
                    user=request.user,
                    task=task,
                    start_time=timezone.now()
                )
                action = 'started'
            
            return JsonResponse({'status': 'success', 'action': action})
        raise Http404("You do not have permission to perform this action.")

class TimeEntryListView(LoginRequiredMixin, ListView):
    model = TimeEntry
    template_name = 'tasks/time_entry_list.html'
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return TimeEntry.objects.none()
        if user.is_superuser:
            return TimeEntry.objects.all().select_related('task', 'invoice', 'user')
        elif user.role == 'admin':
            return TimeEntry.objects.filter(task__created_by=user).select_related('task', 'invoice', 'user')
        elif user.role == 'staff' and user.created_by:
            return TimeEntry.objects.filter(task__created_by=user.created_by).select_related('task', 'invoice', 'user')
        return TimeEntry.objects.filter(user=user).select_related('task', 'invoice', 'user')

class TimeEntryCreateView(LoginRequiredMixin, CreateView):
    model = TimeEntry
    form_class = TimeEntryForm
    template_name = 'tasks/time_entry_form.html'
    success_url = reverse_lazy('tasks:time_entry_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class RecurringTaskListView(LoginRequiredMixin, ListView):
    model = RecurringTask
    template_name = 'tasks/recurring_task_list.html'
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return RecurringTask.objects.none()
        if user.is_superuser:
            return RecurringTask.objects.all().select_related('base_task', 'recurrence', 'base_task__created_by')
        elif user.role == 'admin':
            return RecurringTask.objects.filter(base_task__created_by=user).select_related('base_task', 'recurrence', 'base_task__created_by')
        elif user.role == 'staff' and user.created_by:
            return RecurringTask.objects.filter(base_task__created_by=user.created_by).select_related('base_task', 'recurrence', 'base_task__created_by')
        return RecurringTask.objects.none()

class RecurringTaskCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = RecurringTask
    form_class = RecurringTaskForm
    template_name = 'tasks/recurring_task_form.html'
    success_url = reverse_lazy('tasks:recurring_task_list')
    
    def test_func(self):
        return self.request.user.role in ['admin', 'manager']
    
    def form_valid(self, form):
        form.instance.base_task.created_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class RecurringTaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = RecurringTask
    form_class = RecurringTaskForm
    template_name = 'tasks/recurring_task_form.html'
    success_url = reverse_lazy('tasks:recurring_task_list')
    
    def test_func(self):
        return self.request.user.role in ['admin', 'manager']
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return RecurringTask.objects.none()
        if user.is_superuser:
            return RecurringTask.objects.all().select_related('base_task', 'recurrence', 'base_task__created_by')
        elif user.role == 'admin':
            return RecurringTask.objects.filter(base_task__created_by=user).select_related('base_task', 'recurrence', 'base_task__created_by')
        elif user.role == 'staff' and user.created_by:
            return RecurringTask.objects.filter(base_task__created_by=user.created_by).select_related('base_task', 'recurrence', 'base_task__created_by')
        return RecurringTask.objects.none()

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAdminOrReadOnly]
    required_permissions = ['tasks.view_task']
    
    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.select_related('project', 'project__client', 'created_by').prefetch_related('assignees')
        if user.is_authenticated and not user.is_superuser:
            if user.role == 'admin':
                return queryset.filter(created_by=user)
            elif user.role == 'staff' and user.created_by:
                return queryset.filter(created_by=user.created_by)
            elif user.role == 'client':
                try:
                    client = Client.objects.get(user=user)
                    return queryset.filter(project__client=client)
                except Client.DoesNotExist:
                    return queryset.none()
            return queryset.filter(Q(assignees=user) | Q(created_by=user))
        return queryset

class TimeEntryViewSet(viewsets.ModelViewSet):
    queryset = TimeEntry.objects.all()
    serializer_class = TimeEntrySerializer
    permission_classes = [IsAdminOrReadOnly]
    required_permissions = ['tasks.view_timeentry']
    
    def get_queryset(self):
        user = self.request.user
        queryset = TimeEntry.objects.select_related('task', 'invoice', 'user')
        if user.is_authenticated and not user.is_superuser:
            if user.role == 'admin':
                return queryset.filter(task__created_by=user)
            elif user.role == 'staff' and user.created_by:
                return queryset.filter(task__created_by=user.created_by)
            return queryset.filter(user=user)
        return queryset

class RecurringTaskViewSet(viewsets.ModelViewSet):
    queryset = RecurringTask.objects.all()
    serializer_class = RecurringTaskSerializer
    permission_classes = [IsAdminOrReadOnly]
    required_permissions = ['tasks.view_recurringtask']
    
    def get_queryset(self):
        user = self.request.user
        queryset = RecurringTask.objects.select_related('base_task', 'recurrence', 'base_task__created_by')
        if user.is_authenticated and not user.is_superuser:
            if user.role == 'admin':
                return queryset.filter(base_task__created_by=user)
            elif user.role == 'staff' and user.created_by:
                return queryset.filter(base_task__created_by=user.created_by)
        return queryset