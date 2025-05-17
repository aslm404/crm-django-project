from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SupportTicket, TicketComment
from django.core.mail import send_mail
from django.conf import settings
import logging
from chat.models import Conversation

logger = logging.getLogger(__name__)

@receiver(post_save, sender=SupportTicket)
def create_ticket_conversation(sender, instance, created, **kwargs):
    if created and instance.client and instance.assigned_to:
        conversation, created = Conversation.objects.get_or_create(
            ticket=instance,
            conversation_type='client',
            client=instance.client,
            defaults={'name': f"Ticket {instance.ticket_number}"}
        )
        if created:
            conversation.participants.add(instance.assigned_to, instance.client.user)
            logger.info(f"Created conversation {conversation.id} for ticket {instance.ticket_number}")

@receiver(post_save, sender=SupportTicket)
def notify_assigned_staff(sender, instance, created, **kwargs):
    if instance.assigned_to:
        if created or (instance.pk and SupportTicket.objects.get(pk=instance.pk).assigned_to != instance.assigned_to):
            subject = f"New Ticket Assigned: {instance.ticket_number}"
            message = f"""You have been assigned to ticket {instance.ticket_number}:
            
Subject: {instance.subject}
Priority: {instance.get_priority_display()}
Status: {instance.get_status_display()}
            
Description:
{instance.description}"""
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [instance.assigned_to.email],
                    fail_silently=False,
                )
                logger.info(f"Sent ticket assignment notification to {instance.assigned_to.email}")
            except Exception as e:
                logger.error(f"Failed to send assignment email: {str(e)}")

@receiver(post_save, sender=TicketComment)
def notify_ticket_update(sender, instance, created, **kwargs):
    if created and not instance.is_internal:
        ticket = instance.ticket
        recipients = set()
        
        if ticket.assigned_to:
            recipients.add(ticket.assigned_to.email)
        if instance.author != ticket.created_by:
            recipients.add(ticket.created_by.email)
        
        subject = f"New Comment on Ticket {ticket.ticket_number}"
        message = f"""New comment by {instance.author.get_full_name()}:
        
{instance.content}
        
View the ticket here: {settings.SITE_URL}/support/tickets/{ticket.id}/"""
        
        for email in recipients:
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                logger.info(f"Sent ticket comment notification to {email}")
            except Exception as e:
                logger.error(f"Failed to send comment email to {email}: {str(e)}")