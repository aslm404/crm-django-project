from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Invoice, RecurringInvoice
from datetime import timedelta

@shared_task
def generate_recurring_invoices():
    from tasks.utils import calculate_next_run, should_stop_recurring
    today = timezone.now().date()
    recurring_invoices = RecurringInvoice.objects.filter(
        is_active=True,
        next_run__lte=today
    ).select_related('base_invoice', 'recurrence')
    
    for recurring_invoice in recurring_invoices:
        if should_stop_recurring(
            recurring_invoice.recurrence,
            recurring_invoice.last_run,
            recurring_invoice.total_runs
        ):
            recurring_invoice.is_active = False
            recurring_invoice.save()
            continue
        
        new_invoice = Invoice.objects.create(
            client=recurring_invoice.base_invoice.client,
            project=recurring_invoice.base_invoice.project,
            issue_date=today,
            due_date=today + timedelta(days=30),
            currency=recurring_invoice.base_invoice.currency,
            tax_rate=recurring_invoice.base_invoice.tax_rate,
            discount=recurring_invoice.base_invoice.discount,
            notes=recurring_invoice.base_invoice.notes,
            terms=recurring_invoice.base_invoice.terms,
            footer=recurring_invoice.base_invoice.footer,
            items=recurring_invoice.base_invoice.items,
            created_by=recurring_invoice.base_invoice.created_by,
            status='draft'
        )
        
        recurring_invoice.last_run = today
        recurring_invoice.next_run = calculate_next_run(recurring_invoice.recurrence, today)
        recurring_invoice.total_runs += 1
        recurring_invoice.save()
    
    return f"Generated {recurring_invoices.count()} recurring invoices"

@shared_task
def send_invoice_reminders():
    due_soon = timezone.now().date() + timedelta(days=3)
    overdue = timezone.now().date()
    due_soon_invoices = Invoice.objects.filter(due_date=due_soon, status='sent')
    overdue_invoices = Invoice.objects.filter(due_date__lt=overdue, status='sent')
    
    for invoice in due_soon_invoices:
        subject = f"Reminder: Invoice {invoice.invoice_number} Due Soon"
        message = f"Invoice {invoice.invoice_number} for {invoice.total} is due on {invoice.due_date}"
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [invoice.client.user.email])
    
    for invoice in overdue_invoices:
        subject = f"Urgent: Invoice {invoice.invoice_number} Overdue"
        message = f"Invoice {invoice.invoice_number} for {invoice.total} was due on {invoice.due_date}"
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [invoice.client.user.email])
    
    return f"Sent {due_soon_invoices.count()} due soon and {overdue_invoices.count()} overdue reminders"