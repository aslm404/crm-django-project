from django.shortcuts import get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from rest_framework import viewsets
from .models import Dashboard, Widget
from .forms import DashboardForm, WidgetForm
from .exporters import ExporterFactory
from .widgets import WidgetFactory
from .serializers import DashboardSerializer, WidgetSerializer
from team.permissions import IsAdminOrReadOnly

class DashboardListView(LoginRequiredMixin, ListView):
    model = Dashboard
    template_name = 'reports/dashboard_list.html'
    context_object_name = 'reports'
    
    def get_queryset(self):
        queryset = Dashboard.objects.select_related('created_by').prefetch_related('widgets')
        if self.request.user.is_authenticated:
            if self.request.user.role == 'admin' or self.request.user.is_superuser:
                return queryset
            elif self.request.user.role == 'client':
                return queryset.filter(
                    Q(widgets__data_source='projects.status', widgets__dashboard__project__client__user=self.request.user) |
                    Q(widgets__data_source='tasks.completion', widgets__dashboard__task__project__client__user=self.request.user) |
                    Q(widgets__data_source='invoices.status', widgets__dashboard__invoice__client__user=self.request.user)
                ).distinct()
            else:
                return queryset.filter(Q(created_by=self.request.user) | Q(is_shared=True))
        return queryset.none()
    
class DashboardCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Dashboard
    form_class = DashboardForm
    template_name = 'reports/dashboard_form.html'
    
    def test_func(self):
        return self.request.user.role in ['admin', 'manager']
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('reports:dashboard_detail', kwargs={'pk': self.object.pk})

class DashboardDetailView(LoginRequiredMixin, DetailView):
    model = Dashboard
    template_name = 'reports/dashboard_detail.html'
    
    def get_object(self):
        obj = super().get_object()
        if not (obj.created_by == self.request.user or obj.is_shared):
            raise PermissionDenied
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['widget_types'] = dict(Widget.WIDGET_TYPES)
        return context

class DashboardUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Dashboard
    form_class = DashboardForm
    template_name = 'reports/dashboard_form.html'
    
    def test_func(self):
        return self.request.user.role in ['admin', 'manager'] or self.get_object().created_by == self.request.user
    
    def get_success_url(self):
        return reverse_lazy('reports:dashboard_detail', kwargs={'pk': self.object.pk})

class WidgetCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Widget
    form_class = WidgetForm
    template_name = 'reports/widget_form.html'
    
    def test_func(self):
        dashboard = Dashboard.objects.get(pk=self.kwargs['dashboard_id'])
        return self.request.user.role in ['admin', 'manager'] or dashboard.created_by == self.request.user
    
    def form_valid(self, form):
        form.instance.dashboard_id = self.kwargs['dashboard_id']
        form.instance.position = Widget.objects.filter(
            dashboard_id=self.kwargs['dashboard_id']
        ).count() + 1
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('reports:dashboard_detail', kwargs={'pk': self.kwargs['dashboard_id']})

class WidgetUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Widget
    form_class = WidgetForm
    template_name = 'reports/widget_form.html'
    
    def test_func(self):
        return self.request.user.role in ['admin', 'manager'] or self.get_object().dashboard.created_by == self.request.user
    
    def get_success_url(self):
        return reverse_lazy('reports:dashboard_detail', kwargs={'pk': self.object.dashboard.pk})

class WidgetDataView(LoginRequiredMixin, View):
    def get(self, request, widget_id):
        widget = get_object_or_404(Widget, pk=widget_id)
        
        # Verify permissions
        if not (widget.dashboard.created_by == request.user or widget.dashboard.is_shared):
            raise PermissionDenied
        if request.user.role == 'client' and widget.data_source not in ['projects.status', 'tasks.completion', 'invoices.status']:
            raise PermissionDenied
        
        try:
            widget_instance = WidgetFactory.create_widget(widget.data_source, widget.config, request.user)
            return JsonResponse(widget_instance.render())
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)

class DashboardExportView(LoginRequiredMixin, View):
    def get(self, request, pk, format):
        dashboard = get_object_or_404(Dashboard, pk=pk)
        
        # Verify permissions
        if not (dashboard.created_by == request.user or dashboard.is_shared):
            raise PermissionDenied
        
        try:
            exporter = ExporterFactory.create_exporter(format, dashboard)
            return exporter.export()
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)

class DashboardViewSet(viewsets.ModelViewSet):
    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer
    permission_classes = [IsAdminOrReadOnly]
    required_permissions = ['reports.view_dashboard']
    
    def get_queryset(self):
        return Dashboard.objects.filter(
            Q(created_by=self.request.user) | Q(is_shared=True)
        )

class WidgetViewSet(viewsets.ModelViewSet):
    queryset = Widget.objects.all()
    serializer_class = WidgetSerializer
    permission_classes = [IsAdminOrReadOnly]
    required_permissions = ['reports.view_widget']