from celery import shared_task
from django.utils import timezone
from .models import SupportTicket
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def escalate_unassigned_tickets():
    """
    Escalate tickets that haven't been assigned within 24 hours
    """
    twenty_four_hours_ago = timezone.now() - timezone.timedelta(hours=24)
    unassigned_tickets = SupportTicket.objects.filter(
        assigned_to__isnull=True,
        created_at__lte=twenty_four_hours_ago,
        status='open'
    )
    
    for ticket in unassigned_tickets:
        if ticket.priority != 'high' and ticket.priority != 'critical':
            ticket.priority = 'high'
            ticket.save()
            
            subject = f"Ticket #{ticket.ticket_number} Escalated"
            message = f"Ticket '{ticket.subject}' has been escalated due to lack of assignment."
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                ['managers@hrportal.com'],
                fail_silently=True
            )
    
    return f"Escalated {unassigned_tickets.count()} tickets"

@shared_task
def close_inactive_tickets():
    """
    Automatically close tickets with no activity for 30 days
    """
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    inactive_tickets = SupportTicket.objects.filter(
        status='resolved',
        updated_at__lte=thirty_days_ago
    )
    
    for ticket in inactive_tickets:
        ticket.status = 'closed'
        ticket.save()
        
        subject = f"Ticket #{ticket.ticket_number} Closed"
        message = f"Your ticket '{ticket.subject}' has been closed due to inactivity."
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [ticket.client.user.email],
            fail_silently=True
        )
    
    return f"Closed {inactive_tickets.count()} inactive tickets"