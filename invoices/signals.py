from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
import logging
from invoices.models import Invoice, Payment

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Invoice)
def send_invoice_to_client(sender, instance, created, **kwargs):
    if instance.status == 'sent' and ('status' in instance.tracker.changed() or created):
        subject = f"New Invoice: {instance.invoice_number}"
        message = f"""Dear {instance.client.company},
        
Please find attached invoice {instance.invoice_number} for {instance.Amount} {instance.currency}.
        
Due Date: {instance.due_date}
        
Thank you for your business!"""
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [instance.client.user.email],
                fail_silently=False,
            )
            logger.info(f"Sent invoice {instance.invoice_number} to {instance.client.user.email}")
        except Exception as e:
            logger.error(f"Failed to send invoice email: {str(e)}")

@receiver(post_save, sender=Payment)
def update_invoice_status(sender, instance, created, **kwargs):
    if created:
        invoice = instance.invoice
        if invoice.status != 'paid':
            invoice.status = 'paid'
            invoice.save()
            logger.info(f"Updated invoice {invoice.invoice_number} to paid status")