from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Task, TimeEntry
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Task)
def notify_assignees_on_task_create(sender, instance, created, **kwargs):
    """
    Send notifications when a task is created or assigned
    """
    if created:
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        
        subject = f"New Task Assigned: {instance.title}"
        message = render_to_string('tasks/emails/task_assigned.html', {
            'task': instance,
            'project': instance.project,
        })
        
        for assignee in instance.assignees.all():
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [assignee.email],
                    html_message=message,
                    fail_silently=False,
                )
                logger.info(f"Sent task notification to {assignee.email}")
            except Exception as e:
                logger.error(f"Failed to send email to {assignee.email}: {str(e)}")
        pass    

@receiver(pre_save, sender=TimeEntry)
def calculate_duration(sender, instance, **kwargs):
    """
    Automatically calculate duration when time entry is saved
    """
    if instance.end_time and instance.start_time:
        instance.duration = instance.end_time - instance.start_time
        logger.debug(f"Calculated duration for time entry {instance.id}: {instance.duration}")