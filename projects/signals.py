from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Project
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Project)
def notify_team_on_project_create(sender, instance, created, **kwargs):
    if created:
        subject = f"New Project Assigned: {instance.title}"
        message = f"You have been added to project {instance.title}.\n\nDescription: {instance.description}"
        
        for member in instance.team_members.all():
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [member.email],
                    fail_silently=False,
                )
                logger.info(f"Sent project notification to {member.email} for project {instance.id}")
            except Exception as e:
                logger.error(f"Failed to send email to {member.email} for project {instance.id}: {str(e)}")

@receiver(pre_save, sender=Project)
def update_project_status(sender, instance, **kwargs):
    if instance.pk:
        original = Project.objects.get(pk=instance.pk)
        if original.status != instance.status:
            logger.info(f"Project {instance.id} status changed from {original.status} to {instance.status}")