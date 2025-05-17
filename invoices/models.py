from django.db import models
from clients.models import Client
from projects.models import Project
from team.models import TeamMember
from decimal import Decimal

def clean_json_value(value):
        if isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, dict):
            return {k: clean_json_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [clean_json_value(v) for v in value]
        return value

class Invoice(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    )

    CRNCY_CHOICES = (
        ('USD', 'USD'),
        ('INR', 'INR'),
        ('GBP', 'GBP'),
    )
    
    invoice_number = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    issue_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    currency = models.CharField(max_length=3, choices=CRNCY_CHOICES, default='USD')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)
    footer = models.TextField(blank=True)
    items = models.JSONField(default=list)  # Stores line items
    created_by = models.ForeignKey(TeamMember, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def calculate_total(self):
        total = sum(
            entry.duration.total_seconds() / 3600 * 100  # $100/hour
            for entry in self.time_entries.filter(is_billed=True)
        )
        self.total_amount = total
        self.save()
        return total
    
    def __str__(self):
        return f"Invoice #{self.id} for {self.client.company}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last_invoice = Invoice.objects.order_by('-id').first()
            new_id = last_invoice.id + 1 if last_invoice else 1
            self.invoice_number = f"INV-{new_id:05d}"

        # Compute total
        self.total = self.subtotal - self.discount + self.tax_amount

        # Sanitize items before saving to JSONField
        self.items = clean_json_value(self.items)

        super().save(*args, **kwargs)

    def get_line_items(self):
        return [
            {
                'description': item['description'],
                'quantity': item['quantity'],
                'unit_price': item['unit_price'],
                'total': float(item['quantity']) * float(item['unit_price']),
            }
            for item in self.items
        ]


    @property
    def subtotal(self):
        return sum(item['quantity'] * item['unit_price'] for item in self.items)
    
    @property
    def tax_amount(self):
        return (self.subtotal - self.discount) * self.tax_rate / 100

class Payment(models.Model):
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
    )
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_date = models.DateField()
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(TeamMember, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment of {self.amount} for Invoice #{self.invoice.id}"

class RecurringInvoice(models.Model):
    base_invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    recurrence = models.ForeignKey('tasks.RecurrencePattern', on_delete=models.CASCADE)
    next_run = models.DateField()
    last_run = models.DateField(null=True, blank=True)
    total_runs = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Recurring: {self.base_invoice.invoice_number}"