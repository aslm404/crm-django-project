from django.db.models import Count, Q, F
from datetime import datetime, timedelta
from .models import Project

def get_project_progress(project):
    """
    Calculate completion percentage for a project
    """
    tasks = project.tasks.all()
    total_tasks = tasks.count()
    if total_tasks == 0:
        return 0
    completed_tasks = tasks.filter(status='completed').count()
    return round((completed_tasks / total_tasks) * 100)

def get_project_burnup_data(project):
    """
    Generate burnup chart data for a project
    """
    history = []
    start_date = project.start_date
    end_date = project.deadline
    current_date = start_date
    
    while current_date <= end_date:
        tasks = project.tasks.filter(created_at__date__lte=current_date)
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status='completed', updated_at__date__lte=current_date).count()
        
        history.append({
            'date': current_date,
            'total': total_tasks,
            'completed': completed_tasks
        })
        current_date += timedelta(days=1)
    
    return history

def get_project_health_stats():
    """
    Get statistics about all projects' health
    """
    return Project.objects.annotate(
        overdue_tasks=Count('tasks', filter=Q(tasks__due_date__lt=datetime.now().date())),
        total_tasks=Count('tasks')
    ).annotate(
        health_score=F('total_tasks') - F('overdue_tasks') * 2
    ).order_by('-health_score')