from django.db.models import Sum, Count
from datetime import datetime, timedelta

def get_client_billing_summary(client):
    from invoices.models import Invoice
    invoices = client.invoices.all()
    total = invoices.aggregate(amount=Sum('total'), count=Count('id'))
    paid = invoices.filter(status='paid').aggregate(amount=Sum('total'))['amount'] or 0
    overdue = invoices.filter(status='sent', due_date__lt=datetime.now().date()).aggregate(amount=Sum('total'))['amount'] or 0
    return {
        'total_invoices': total['count'],
        'total_amount': total['amount'] or 0,
        'paid_amount': paid,
        'overdue_amount': overdue,
        'outstanding_amount': (total['amount'] or 0) - paid
    }

def get_client_project_stats(client):
    projects = client.project_set.all()
    total = projects.count()
    if total == 0:
        return {
            'total_projects': 0,
            'completed_projects': 0,
            'active_projects': 0,
            'completion_rate': 0
        }
    completed = projects.filter(status='completed').count()
    active = projects.filter(status='in_progress').count()
    return {
        'total_projects': total,
        'completed_projects': completed,
        'active_projects': active,
        'completion_rate': round((completed / total) * 100)
    }

def get_client_activity_timeline(client, days=90):
    from invoices.models import Invoice
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    timeline = []
    projects = client.project_set.filter(created_at__range=(start_date, end_date))
    for p in projects:
        timeline.append({
            'date': p.created_at,
            'type': 'project',
            'title': f"New project: {p.title}",
            'status': p.status
        })
    invoices = client.invoices.filter(issue_date__range=(start_date, end_date))
    for i in invoices:
        timeline.append({
            'date': i.issue_date,
            'type': 'invoice',
            'title': f"Invoice {i.invoice_number}",
            'status': i.status,
            'amount': i.total
        })
    timeline.sort(key=lambda x: x['date'], reverse=True)
    return timeline