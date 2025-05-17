from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import Http404
from clients.models import Client
from .models import SupportTicket, TicketComment, TicketCategory, TicketStatusUpdate
from .forms import TicketForm, TicketCommentForm, TicketStatusForm, TicketCategoryForm
from rest_framework import viewsets
from .serializers import SupportTicketSerializer, TicketCommentSerializer, TicketCategorySerializer
from team.permissions import IsAdminOrReadOnly

class TicketListView(LoginRequiredMixin, ListView):
    model = SupportTicket
    template_name = 'support/ticket_list.html'
    context_object_name = 'tickets'
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return SupportTicket.objects.none()
        queryset = SupportTicket.objects.select_related('client', 'assigned_to', 'created_by', 'category')
        if user.is_superuser:
            return queryset
        elif user.role == 'admin':
            return queryset.filter(created_by=user)
        elif user.role == 'staff' and user.created_by:
            return queryset.filter(created_by=user.created_by)
        elif user.role == 'client':
            try:
                client = Client.objects.get(user=user)
                return queryset.filter(client=client)
            except Client.DoesNotExist:
                return queryset.none()
        return queryset.filter(assigned_to=user)

class TicketCreateView(LoginRequiredMixin, CreateView):
    model = SupportTicket
    form_class = TicketForm
    template_name = 'support/ticket_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        if self.request.user.role == 'client':
            form.instance.client = Client.objects.filter(user=self.request.user).first()
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('support:ticket_detail', kwargs={'pk': self.object.pk})

class TicketDetailView(LoginRequiredMixin, DetailView):
    model = SupportTicket
    template_name = 'support/ticket_detail.html'
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return SupportTicket.objects.none()
        queryset = SupportTicket.objects.select_related('client', 'assigned_to', 'created_by', 'category')
        if user.is_superuser:
            return queryset
        elif user.role == 'admin':
            return queryset.filter(created_by=user)
        elif user.role == 'staff' and user.created_by:
            return queryset.filter(created_by=user.created_by)
        elif user.role == 'client':
            try:
                client = Client.objects.get(user=user)
                return queryset.filter(client=client)
            except Client.DoesNotExist:
                return queryset.none()
        return queryset.filter(assigned_to=user)
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        if user.is_superuser or \
           (user.role == 'admin' and obj.created_by == user) or \
           (user.role == 'staff' and user.created_by and obj.created_by == user.created_by) or \
           (user.role == 'client' and hasattr(user, 'client_profile') and obj.client == user.client_profile) or \
           (obj.assigned_to == user):
            return obj
        raise Http404("You do not have permission to view this ticket.")

class TicketStatusUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = SupportTicket
    form_class = TicketStatusForm
    template_name = 'support/ticket_status_update.html'
    
    def test_func(self):
        return self.request.user.role in ['admin', 'staff']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        old_status = self.object.status
        response = super().form_valid(form)
        if form.instance.status == 'resolved' and old_status != 'resolved':
            form.instance.resolved_at = timezone.now()
        if old_status != form.instance.status:
            TicketStatusUpdate.objects.create(
                ticket=self.object,
                changed_by=self.request.user,
                old_status=old_status,
                new_status=form.instance.status
            )
        return response
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return SupportTicket.objects.none()
        if user.is_superuser:
            return SupportTicket.objects.all().select_related('client', 'assigned_to', 'created_by', 'category')
        elif user.role == 'admin':
            return SupportTicket.objects.filter(created_by=user).select_related('client', 'assigned_to', 'created_by', 'category')
        elif user.role == 'staff' and user.created_by:
            return SupportTicket.objects.filter(created_by=user.created_by).select_related('client', 'assigned_to', 'created_by', 'category')
        return SupportTicket.objects.filter(assigned_to=user).select_related('client', 'assigned_to', 'created_by', 'category')
    
    def get_success_url(self):
        return reverse_lazy('support:ticket_detail', kwargs={'pk': self.object.pk})

class AddCommentView(LoginRequiredMixin, CreateView):
    model = TicketComment
    form_class = TicketCommentForm
    template_name = 'support/add_comment.html'
    
    def form_valid(self, form):
        ticket = get_object_or_404(SupportTicket, pk=self.kwargs['pk'])
        user = self.request.user
        if user.is_superuser or \
           (user.role == 'admin' and ticket.created_by == user) or \
           (user.role == 'staff' and user.created_by and ticket.created_by == user.created_by) or \
           (user.role == 'client' and hasattr(user, 'client_profile') and ticket.client == user.client_profile) or \
           (ticket.assigned_to == user):
            form.instance.ticket = ticket
            form.instance.author = self.request.user
            return super().form_valid(form)
        raise Http404("You do not have permission to comment on this ticket.")
    
    def get_success_url(self):
        return reverse_lazy('support:ticket_detail', kwargs={'pk': self.kwargs['pk']})

class TicketCategoryListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = TicketCategory
    template_name = 'support/category_list.html'
    
    def test_func(self):
        return self.request.user.role in ['admin']

class TicketCategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = TicketCategory
    form_class = TicketCategoryForm
    template_name = 'support/category_form.html'
    success_url = reverse_lazy('support:category_list')
    
    def test_func(self):
        return self.request.user.role in ['admin']

class SupportTicketViewSet(viewsets.ModelViewSet):
    queryset = SupportTicket.objects.all()
    serializer_class = SupportTicketSerializer
    permission_classes = [IsAdminOrReadOnly]
    required_permissions = ['support.view_supportticket']
    
    def get_queryset(self):
        user = self.request.user
        queryset = SupportTicket.objects.select_related('client', 'assigned_to', 'created_by', 'category')
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
            return queryset.filter(assigned_to=user)
        return queryset

class TicketCommentViewSet(viewsets.ModelViewSet):
    queryset = TicketComment.objects.all()
    serializer_class = TicketCommentSerializer
    permission_classes = [IsAdminOrReadOnly]
    required_permissions = ['support.view_ticketcomment']
    
    def get_queryset(self):
        user = self.request.user
        queryset = TicketComment.objects.select_related('ticket', 'author')
        if user.is_authenticated and not user.is_superuser:
            if user.role == 'admin':
                return queryset.filter(ticket__created_by=user)
            elif user.role == 'staff' and user.created_by:
                return queryset.filter(ticket__created_by=user.created_by)
            elif user.role == 'client':
                try:
                    client = Client.objects.get(user=user)
                    return queryset.filter(ticket__client=client, is_internal=False)
                except Client.DoesNotExist:
                    return queryset.none()
            return queryset.filter(author=user)
        return queryset

class TicketCategoryViewSet(viewsets.ModelViewSet):
    queryset = TicketCategory.objects.all()
    serializer_class = TicketCategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    required_permissions = ['support.view_ticketcategory']