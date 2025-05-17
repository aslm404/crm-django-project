from datetime import datetime, timedelta
from django.db.models import Sum
from dateutil.relativedelta import relativedelta
from invoices.models import Invoice

def generate_invoice_number(last_invoice=None):
    if not last_invoice:
        return "INV-00001"
    new_id = last_invoice.id + 1
    return f"INV-{new_id:05d}"

def calculate_invoice_totals(invoice):
    return {
        'subtotal': invoice.subtotal,
        'tax_amount': invoice.tax_amount,
        'total': invoice.total
    }

def get_revenue_report(months=12):
    end_date = datetime.now().date()
    start_date = end_date - relativedelta(months=months)
    months_data = []
    current_date = start_date
    
    while current_date <= end_date:
        month_start = current_date.replace(day=1)
        month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)
        paid_invoices = Invoice.objects.filter(
            status='paid',
            issue_date__range=(month_start, month_end)
        )
        month_total = paid_invoices.aggregate(total=Sum('total'))['total'] or 0
        months_data.append({
            'month': month_start.strftime('%Y-%m'),
            'total': month_total,
            'invoice_count': paid_invoices.count()
        })
        current_date = month_start + relativedelta(months=1)
    
    return months_data