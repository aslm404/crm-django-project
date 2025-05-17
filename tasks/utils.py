from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Sum, Count, Q
from .models import Task, TimeEntry

def calculate_task_duration(task):
    """
    Calculate total time spent on a task
    """
    total = TimeEntry.objects.filter(task=task).aggregate(
        total_duration=Sum('duration')
    )['total_duration'] or timedelta(0)
    return total

def get_task_completion_rate(user=None):
    """
    Calculate task completion rate for a user or all users
    """
    queryset = Task.objects.all()
    if user:
        queryset = queryset.filter(assignees=user)
    
    stats = queryset.aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed'))
    )
    
    if stats['total'] == 0:
        return 0
    return round((stats['completed'] / stats['total']) * 100)

def calculate_next_run(recurrence, last_run=None):
    """
    Calculate next run date for recurring tasks
    """
    if not last_run:
        last_run = datetime.now().date()
    
    if recurrence.interval == 'daily':
        return last_run + timedelta(days=recurrence.frequency)
    elif recurrence.interval == 'weekly':
        return last_run + timedelta(weeks=recurrence.frequency)
    elif recurrence.interval == 'monthly':
        return last_run + relativedelta(months=+recurrence.frequency)
    elif recurrence.interval == 'yearly':
        return last_run + relativedelta(years=+recurrence.frequency)
    return None

def should_stop_recurring(recurrence, last_run, total_runs):
    if recurrence.max_occurrences and total_runs >= recurrence.max_occurrences:
        return True
    if recurrence.end_date and last_run and last_run >= recurrence.end_date:
        return True
    return False

def get_user_workload(user, days=30):
    """
    Get workload statistics for a user
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    time_entries = TimeEntry.objects.filter(
        user=user,
        start_time__range=(start_date, end_date)
    )
    
    total_hours = time_entries.aggregate(
        total=Sum('duration')
    )['total'] or timedelta(0)
    
    projects = time_entries.values(
        'task__project__title'
    ).annotate(
        hours=Sum('duration')
    ).order_by('-hours')
    
    return {
        'total_hours': total_hours.total_seconds() / 3600,
        'projects': projects,
        'start_date': start_date,
        'end_date': end_date
    }