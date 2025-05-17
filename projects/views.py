from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import Http404
from .models import Project
from .forms import ProjectForm
from rest_framework import viewsets
from .serializers import ProjectSerializer
from .permissions import ProjectPermission
from team.models import TeamMember
from clients.models import Client

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/list.html'
    context_object_name = 'projects'
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Project.objects.none()
        if user.is_superuser:
            return Project.objects.all().select_related('client', 'created_by').prefetch_related('team_members')
        elif user.role == 'admin':
            return Project.objects.filter(created_by=user).select_related('client', 'created_by').prefetch_related('team_members')
        elif user.role == 'staff' and user.created_by:
            return Project.objects.filter(created_by=user.created_by).select_related('client', 'created_by').prefetch_related('team_members')
        elif user.role == 'client':
            try:
                client = Client.objects.get(user=user)
                return Project.objects.filter(client=client).select_related('client', 'created_by').prefetch_related('team_members')
            except Client.DoesNotExist:
                return Project.objects.none()
        return Project.objects.filter(team_members=user).select_related('client', 'created_by').prefetch_related('team_members')

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('projects:detail', kwargs={'pk': self.object.pk})

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/detail.html'
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Project.objects.none()
        if user.is_superuser:
            return Project.objects.all().select_related('client', 'created_by').prefetch_related('team_members')
        elif user.role == 'admin':
            return Project.objects.filter(created_by=user).select_related('client', 'created_by').prefetch_related('team_members')
        elif user.role == 'staff' and user.created_by:
            return Project.objects.filter(created_by=user.created_by).select_related('client', 'created_by').prefetch_related('team_members')
        elif user.role == 'client':
            try:
                client = Client.objects.get(user=user)
                return Project.objects.filter(client=client).select_related('client', 'created_by').prefetch_related('team_members')
            except Client.DoesNotExist:
                return Project.objects.none()
        return Project.objects.filter(team_members=user).select_related('client', 'created_by').prefetch_related('team_members')
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        if user.is_superuser or \
           (user.role == 'admin' and obj.created_by == user) or \
           (user.role == 'staff' and user.created_by and obj.created_by == user.created_by) or \
           (user.role == 'client' and hasattr(user, 'client_profile') and obj.client == user.client_profile) or \
           (user in obj.team_members.all()):
            return obj
        raise Http404("You do not have permission to view this project.")

class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Project.objects.none()
        if user.is_superuser:
            return Project.objects.all().select_related('client', 'created_by').prefetch_related('team_members')
        elif user.role == 'admin':
            return Project.objects.filter(created_by=user).select_related('client', 'created_by').prefetch_related('team_members')
        elif user.role == 'staff' and user.created_by:
            return Project.objects.filter(created_by=user.created_by).select_related('client', 'created_by').prefetch_related('team_members')
        return Project.objects.none()
    
    def get_success_url(self):
        return reverse_lazy('projects:detail', kwargs={'pk': self.object.pk})

class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'projects/confirm_delete.html'
    success_url = reverse_lazy('projects:list')
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Project.objects.none()
        if user.is_superuser or user.role == 'admin':
            return Project.objects.filter(created_by=user).select_related('client', 'created_by').prefetch_related('team_members')
        return Project.objects.none()

class ProjectTeamUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    fields = ['team_members']
    template_name = 'projects/team_update.html'
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Project.objects.none()
        if user.is_superuser or user.role == 'admin':
            return Project.objects.filter(created_by=user).select_related('client', 'created_by').prefetch_related('team_members')
        return Project.objects.none()
    
    def get_success_url(self):
        return reverse_lazy('projects:detail', kwargs={'pk': self.object.pk})

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [ProjectPermission]
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset().select_related('client', 'created_by').prefetch_related('team_members')
        if user.is_authenticated and not user.is_superuser:
            if user.role == 'admin':
                return queryset.filter(created_by=user)
            elif user.role == 'staff' and user.created_by:
                return queryset.filter(created_by=user.created_by)
            elif user.role == 'client':
                try:
                    client = Client.objects.get(user=user)
                    return queryset.filter(client=client)
                except Client.DoesNotExist:
                    return queryset.none()
            return queryset.filter(team_members=user)
        return queryset