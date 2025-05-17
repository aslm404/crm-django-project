from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.contrib import messages
from .models import Client, ClientNote, ClientFile
from .forms import ClientForm, ClientNoteForm, ClientFileForm
from team.models import TeamMember
from rest_framework import viewsets
from .serializers import ClientSerializer, ClientNoteSerializer, ClientFileSerializer
from .permissions import ClientPermission
import logging

logger = logging.getLogger(__name__)

class ClientAccessMixin:
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        user = request.user
        if user.is_superuser or \
           (user.role in ['admin', 'staff'] and obj.user.created_by == user) or \
           (user.role == 'staff' and user.created_by and obj.user.created_by == user.created_by) or \
           (obj.user == user):
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied

class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = 'clients/list.html'
    context_object_name = 'clients'
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Client.objects.none()
        if user.is_superuser:
            return Client.objects.all().select_related('user').distinct()
        elif user.role == 'admin':
            return Client.objects.filter(user__created_by=user).select_related('user').distinct()
        elif user.role == 'staff' and user.created_by:
            return Client.objects.filter(user__created_by=user.created_by).select_related('user').distinct()
        elif user.role == 'client':
            return Client.objects.filter(user=user).select_related('user').distinct()
        return Client.objects.none()

class ClientCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/form.html'
    success_url = reverse_lazy('clients:list')

    def test_func(self):
        return self.request.user.role == 'admin'

    def form_valid(self, form):
        user = form.cleaned_data.get('user')

        # Remove duplicate check:
        # if Client.objects.filter(user=user).exists():
        #     messages.error(self.request, f"A client already exists for user {user.email}.")
        #     logger.warning(f"Attempted to create duplicate client for user {user.email} by admin {self.request.user.username}")
        #     return self.form_invalid(form)

        # Set created_by for the TeamMember if new
        if not user.created_by:
            user.created_by = self.request.user
            user.save()

        response = super().form_valid(form)
        messages.success(self.request, f"Client {form.instance.company} created successfully.")
        logger.info(f"Client {form.instance.company} created for user {user.email} by admin {self.request.user.username}")
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class ClientDetailView(LoginRequiredMixin, ClientAccessMixin, DetailView):
    model = Client
    template_name = 'clients/detail.html'
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Client.objects.none()
        if user.is_superuser:
            return Client.objects.all().select_related('user')
        elif user.role == 'admin':
            return Client.objects.filter(user__created_by=user).select_related('user')
        elif user.role == 'staff' and user.created_by:
            return Client.objects.filter(user__created_by=user.created_by).select_related('user')
        elif user.role == 'client':
            return Client.objects.filter(user=user).select_related('user')
        return Client.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projects'] = self.object.projects.all().select_related('client', 'created_by')
        context['notes'] = self.object.notes.all().select_related('created_by')
        context['files'] = self.object.files.all().select_related('uploaded_by')
        return context

class ClientUpdateView(LoginRequiredMixin, ClientAccessMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Client.objects.none()
        if user.is_superuser:
            return Client.objects.all().select_related('user')
        elif user.role == 'admin':
            return Client.objects.filter(user__created_by=user).select_related('user')
        elif user.role == 'staff' and user.created_by:
            return Client.objects.filter(user__created_by=user.created_by).select_related('user')
        elif user.role == 'client':
            return Client.objects.filter(user=user).select_related('user')
        return Client.objects.none()
    
    def get_success_url(self):
        return reverse_lazy('clients:detail', kwargs={'pk': self.object.pk})

class ClientPortalView(LoginRequiredMixin, ClientAccessMixin, DetailView):
    model = Client
    template_name = 'clients/portal.html'
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Client.objects.none()
        if user.is_superuser:
            return Client.objects.all().select_related('user')
        elif user.role == 'admin':
            return Client.objects.filter(user__created_by=user).select_related('user')
        elif user.role == 'staff' and user.created_by:
            return Client.objects.filter(user__created_by=user.created_by).select_related('user')
        elif user.role == 'client':
            return Client.objects.filter(user=user).select_related('user')
        return Client.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_projects'] = self.object.projects.filter(status='in_progress').select_related('client', 'created_by')
        context['recent_invoices'] = self.object.invoices.order_by('-issue_date')[:5].select_related('client', 'created_by')
        return context

class ClientNoteCreateView(LoginRequiredMixin, CreateView):
    model = ClientNote
    form_class = ClientNoteForm
    template_name = 'clients/note_form.html'
    
    def form_valid(self, form):
        form.instance.client_id = self.kwargs['client_pk']
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Client.objects.none()
        if user.is_superuser:
            return Client.objects.all().select_related('user')
        elif user.role == 'admin':
            return Client.objects.filter(user__created_by=user).select_related('user')
        elif user.role == 'staff' and user.created_by:
            return Client.objects.filter(user__created_by=user.created_by).select_related('user')
        return Client.objects.none()
    
    def get_success_url(self):
        return reverse_lazy('clients:detail', kwargs={'pk': self.kwargs['client_pk']})

class ClientNoteUpdateView(LoginRequiredMixin, UpdateView):
    model = ClientNote
    form_class = ClientNoteForm
    template_name = 'clients/note_form.html'
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return ClientNote.objects.none()
        if user.is_superuser:
            return ClientNote.objects.all().select_related('client', 'created_by')
        elif user.role == 'admin':
            return ClientNote.objects.filter(client__user__created_by=user).select_related('client', 'created_by')
        elif user.role == 'staff' and user.created_by:
            return ClientNote.objects.filter(client__user__created_by=user.created_by).select_related('client', 'created_by')
        return ClientNote.objects.none()
    
    def get_success_url(self):
        return reverse_lazy('clients:detail', kwargs={'pk': self.object.client.pk})

class ClientFileUploadView(LoginRequiredMixin, CreateView):
    model = ClientFile
    form_class = ClientFileForm
    template_name = 'clients/file_upload.html'
    
    def form_valid(self, form):
        form.instance.client_id = self.kwargs['client_pk']
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Client.objects.none()
        if user.is_superuser:
            return Client.objects.all().select_related('user')
        elif user.role == 'admin':
            return Client.objects.filter(user__created_by=user).select_related('user')
        elif user.role == 'staff' and user.created_by:
            return Client.objects.filter(user__created_by=user.created_by).select_related('user')
        return Client.objects.none()
    
    def get_success_url(self):
        return reverse_lazy('clients:detail', kwargs={'pk': self.kwargs['client_pk']})

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [ClientPermission]
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset().select_related('user').distinct()
        if user.is_authenticated and not user.is_superuser:
            if user.role == 'admin':
                return queryset.filter(user__created_by=user)
            elif user.role == 'staff' and user.created_by:
                return queryset.filter(user__created_by=user.created_by)
            elif user.role == 'client':
                return queryset.filter(user=user)
        return queryset

class ClientNoteViewSet(viewsets.ModelViewSet):
    queryset = ClientNote.objects.all()
    serializer_class = ClientNoteSerializer
    permission_classes = [ClientPermission]
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset().select_related('client', 'created_by')
        if user.is_authenticated and not user.is_superuser:
            if user.role == 'admin':
                return queryset.filter(client__user__created_by=user)
            elif user.role == 'staff' and user.created_by:
                return queryset.filter(client__user__created_by=user.created_by)
            elif user.role == 'client':
                return queryset.filter(client__user=user)
        return queryset

class ClientFileViewSet(viewsets.ModelViewSet):
    queryset = ClientFile.objects.all()
    serializer_class = ClientFileSerializer
    permission_classes = [ClientPermission]
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset().select_related('client', 'uploaded_by')
        if user.is_authenticated and not user.is_superuser:
            if user.role == 'admin':
                return queryset.filter(client__user__created_by=user)
            elif user.role == 'staff' and user.created_by:
                return queryset.filter(client__user__created_by=user.created_by)
            elif user.role == 'client':
                return queryset.filter(client__user=user)
        return queryset