from celery import shared_task
from .models import Project
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)

@shared_task
def update_all_project_progress():
    projects = Project.objects.filter(
        status__in=['planned', 'in_progress']
    ).prefetch_related('tasks')
    
    for project in projects:
        project.save()
    
    logger.info(f"Updated progress for {projects.count()} projects")
    return f"Updated progress for {projects.count()} projects"

@shared_task
def send_project_status_updates():
    active_projects = Project.objects.filter(
        status__in=['in_progress']
    ).prefetch_related('tasks', 'team_members')
    
    for project in active_projects:
        recipients = list(project.team_members.values_list('email', flat=True))
        if project.client.user.email not in recipients:
            recipients.append(project.client.user.email)
        
        subject = f"Weekly Update: {project.title}"
        text_content = f"Here's the weekly update for {project.title}"
        try:
            html_content = render_to_string('emails/project_update.html', {
                'project': project,
                'tasks': project.tasks.all()
            })
            email = EmailMultiAlternatives(
                subject,
                text_content,
                'updates@hrportal.com',
                recipients
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            logger.info(f"Sent status update for project {project.id} to {len(recipients)} recipients")
        except Exception as e:
            logger.error(f"Failed to send status update for project {project.id}: {str(e)}")
    
    return f"Sent updates for {active_projects.count()} projects"