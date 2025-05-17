from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import Task, RecurringTask, TimeEntry
from projects.models import Project
from team.models import TeamMember

@shared_task
def generate_recurring_tasks():
    """
    Generate tasks from recurring task templates
    """
    from .utils import calculate_next_run, should_stop_recurring
    
    today = timezone.now().date()
    recurring_tasks = RecurringTask.objects.filter(
        is_active=True,
        next_run__lte=today
    ).select_related('base_task', 'recurrence')
    
    for recurring_task in recurring_tasks:
        if should_stop_recurring(
            recurring_task.recurrence,
            recurring_task.last_run,
            recurring_task.total_runs
        ):
            recurring_task.is_active = False
            recurring_task.save()
            continue
        
        new_task = Task.objects.create(
            title=f"{recurring_task.base_task.title} ({today.strftime('%Y-%m-%d')})",
            description=recurring_task.base_task.description,
            project=recurring_task.base_task.project,
            status='todo',
            priority=recurring_task.base_task.priority,
            due_date=recurring_task.base_task.due_date,
            created_by=recurring_task.base_task.created_by,
            estimated_duration=recurring_task.base_task.estimated_duration
        )
        new_task.assignees.set(recurring_task.base_task.assignees.all())
        
        recurring_task.last_run = today
        recurring_task.next_run = calculate_next_run(
            recurring_task.recurrence,
            today
        )
        recurring_task.total_runs += 1
        recurring_task.save()
    
    return f"Generated {recurring_tasks.count()} recurring tasks"

@shared_task
def send_due_date_reminders():
    """
    Send email reminders for tasks due soon or overdue
    """
    tomorrow = timezone.now().date() + timedelta(days=1)
    overdue_tasks = Task.objects.filter(
        due_date__lt=timezone.now().date(),
        status__in=['todo', 'in_progress']
    ).select_related('project', 'created_by')
    
    due_soon_tasks = Task.objects.filter(
        due_date=tomorrow,
        status__in=['todo', 'in_progress']
    ).select_related('project', 'created_by')
    
    for task in overdue_tasks:
        recipients = list(task.assignees.values_list('email', flat=True))
        if task.created_by.email not in recipients:
            recipients.append(task.created_by.email)
        
        subject = f"Overdue Task: {task.title}"
        message = render_to_string('tasks/emails/task_overdue.html', {
            'task': task,
            'days_overdue': (timezone.now().date() - task.due_date).days
        })
        
        send_mail(
            subject,
            message,
            'notifications@hrportal.com',
            recipients,
            html_message=message,
            fail_silently=True
        )
    
    for task in due_soon_tasks:
        recipients = list(task.assignees.values_list('email', flat=True))
        if task.created_by.email not in recipients:
            recipients.append(task.created_by.email)
        
        subject = f"Task Due Tomorrow: {task.title}"
        message = render_to_string('tasks/emails/task_due_soon.html', {
            'task': task
        })
        
        send_mail(
            subject,
            message,
            'notifications@hrportal.com',
            recipients,
            html_message=message,
            fail_silently=True
        )
    
    return f"Sent {overdue_tasks.count()} overdue and {due_soon_tasks.count()} due soon reminders"

@shared_task
def stop_long_running_timers():
    """
    Stop any timers that have been running for more than 12 hours
    """
    twelve_hours_ago = timezone.now() - timedelta(hours=12)
    long_running = TimeEntry.objects.filter(
        end_time__isnull=True,
        start_time__lte=twelve_hours_ago
    )
    
    for entry in long_running:
        entry.end_time = entry.start_time + timedelta(hours=12)
        entry.save()
    
    return f"Stopped {long_running.count()} long-running timers"

@shared_task
def calculate_task_time_estimate(task_id):
    """
    Calculate time estimate for a task based on historical data
    """
    from django.db.models import Avg
    
    task = Task.objects.get(pk=task_id)
    similar_tasks = Task.objects.filter(
        project=task.project,
        status='completed'
    )
    
    if similar_tasks.exists():
        avg_time = similar_tasks.aggregate(
            avg_time=Avg('time_entries__duration')
        )['avg_time']
        if avg_time:
            task.estimated_duration = avg_time
            task.save()
    
    return f"Updated time estimate for task {task_id}"

@shared_task
def sync_task_status_to_project(task_id):
    """
    Update project status based on task completion
    """
    task = Task.objects.get(pk=task_id)
    project = task.project
    
    total_tasks = project.tasks.count()
    completed_tasks = project.tasks.filter(status='completed').count()
    
    if completed_tasks == 0:
        project.status = 'planned'
    elif completed_tasks == total_tasks:
        project.status = 'completed'
    else:
        project.status = 'in_progress'
    
    project.save()
    return f"Updated status for project {project.id} based on task {task_id}"