from .utils import (
    get_project_status_data, get_task_completion_data,
    get_team_performance_data, get_client_billing_data
)
from django.db.models import Sum, Count
from datetime import datetime, timedelta
from tasks.models import TimeEntry
from invoices.models import Invoice
from django.core.exceptions import ImproperlyConfigured
from support.utils import get_ticket_stats

class BaseWidget:
    """Abstract base class for all widgets"""
    def __init__(self, data_source, config=None, user=None):
        self.data_source = data_source
        self.config = config or {}
        self.user = user
    
    def get_data(self):
        """Must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement get_data()")
    
    def render(self):
        """Return data in format ready for frontend"""
        data = self.get_data()
        return {
            'data': data,
            'config': self.config
        }

class ProjectStatusWidget(BaseWidget):
    """Widget showing project status distribution"""
    def get_data(self):
        return get_project_status_data(self.user)

class TaskCompletionWidget(BaseWidget):
    """Widget showing task completion by project"""
    def get_data(self):
        return get_task_completion_data(self.user)

class TimeTrackingWidget(BaseWidget):
    """Widget showing time tracking data"""
    def get_data(self):
        days = self.config.get('days', 30)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        queryset = TimeEntry.objects.filter(
            start_time__gte=start_date
        )
        if self.user and self.user.role == 'client':
            queryset = queryset.filter(task__project__client__user=self.user)
        
        return list(queryset.values(
            'task__project__title'
        ).annotate(
            total_hours=Sum('duration') / timedelta(hours=1)
        ).order_by('-total_hours'))

class InvoiceStatusWidget(BaseWidget):
    """Widget showing invoice status and amounts"""
    def get_data(self):
        queryset = Invoice.objects.all()
        if self.user and self.user.role == 'client':
            queryset = queryset.filter(client__user=self.user)
        return list(queryset.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('total_amount')
        ).order_by('status'))

class TeamPerformanceWidget(BaseWidget):
    """Widget showing team performance metrics"""
    def get_data(self):
        return get_team_performance_data(self.user)

class ClientBillingWidget(BaseWidget):
    """Widget showing client billing summary"""
    def get_data(self):
        return get_client_billing_data(self.user)

class WidgetFactory:
    """Factory class to create appropriate widget based on data source"""
    WIDGET_MAP = {
        'projects.status': ProjectStatusWidget,
        'tasks.completion': TaskCompletionWidget,
        'time.tracking': TimeTrackingWidget,
        'invoices.status': InvoiceStatusWidget,
        'team.performance': TeamPerformanceWidget,
        'clients.billing': ClientBillingWidget,
    }
    
    @classmethod
    def create_widget(cls, data_source, config=None, user=None):
        widget_class = cls.WIDGET_MAP.get(data_source)
        if not widget_class:
            raise ValueError(f"Unknown data source: {data_source}")
        return widget_class(data_source, config, user)
    
    @classmethod
    def get_available_data_sources(cls):
        return list(cls.WIDGET_MAP.keys())
    
class TicketStatsWidget(BaseWidget):
    """Widget showing ticket statistics"""
    def __init__(self, data_source, config=None, user=None):
        super().__init__(data_source, config, user)
    
    def get_data(self):
        return get_ticket_stats(self.user)

WIDGET_MAP = {
    'support.stats': TicketStatsWidget,
}    