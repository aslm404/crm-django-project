from django.db.models import Sum, Count, Avg, Q
from datetime import datetime, timedelta
from invoices.models import Invoice
from projects.models import Project
from tasks.models import Task, TimeEntry

def get_project_status_data(user=None):
    """
    Get data for project status chart
    """
    queryset = Project.objects.all()
    if user and user.role == 'client':
        queryset = queryset.filter(client__user=user)
    return list(queryset.values('status').annotate(
        count=Count('id'),
        total_budget=Sum('budget')
    ).order_by('status'))

def get_task_completion_data(user=None):
    """
    Get data for task completion by project
    """
    queryset = Task.objects.all()
    if user and user.role == 'client':
        queryset = queryset.filter(project__client__user=user)
    return list(queryset.values(
        'project__title'
    ).annotate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed'))
    ).order_by('project__title'))

def get_team_performance_data(user=None, days=30):
    """
    Get team performance metrics
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    queryset = TimeEntry.objects.filter(
        start_time__range=(start_date, end_date)
    )
    if user and user.role == 'client':
        queryset = queryset.filter(task__project__client__user=user)
    
    return list(queryset.values(
        'user__username', 'user__first_name', 'user__last_name'
    ).annotate(
        hours=Sum('duration') / timedelta(hours=1),
        tasks_completed=Count('task', distinct=True, filter=Q(task__status='completed')),
        efficiency=Avg('task__complexity')
    ).order_by('-hours'))

def get_client_billing_data(user=None):
    """
    Get data for client billing report
    """
    queryset = Invoice.objects.all()
    if user and user.role == 'client':
        queryset = queryset.filter(client__user=user)
    return list(queryset.values(
        'client__company', 'client__user__email'
    ).annotate(
        invoice_count=Count('id'),
        total_billed=Sum('total_amount'),
        paid_amount=Sum('total_amount', filter=Q(status='paid')),
        overdue_amount=Sum('total_amount', filter=Q(status='sent', due_date__lt=datetime.now().date()))
    ).order_by('-total_billed'))

def export_report_to_csv(report_data, fields):
    """
    Export report data to CSV format
    """
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows(report_data)
    
    return output.getvalue()