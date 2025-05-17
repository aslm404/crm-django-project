from django.db.models import Count, Q, F, Avg
from datetime import datetime, timedelta
from support.models import SupportTicket

def get_ticket_stats(assigned_to=None):
    """
    Get ticket statistics for a support agent or all agents
    """
    queryset = SupportTicket.objects.all()
    if assigned_to:
        queryset = queryset.filter(assigned_to=assigned_to)
    
    stats = queryset.aggregate(
        total=Count('id'),
        open=Count('id', filter=Q(status='open')),
        in_progress=Count('id', filter=Q(status='in_progress')),
        resolved=Count('id', filter=Q(status='resolved'))
    )
    
    stats['resolution_rate'] = round((stats['resolved'] / stats['total']) * 100) if stats['total'] > 0 else 0
    return stats

def get_ticket_response_times(days=30):
    """
    Calculate average response times for tickets
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    resolved_tickets = SupportTicket.objects.filter(
        status='resolved',
        resolved_at__range=(start_date, end_date)
    )
    
    avg_response = resolved_tickets.annotate(
        response_time=F('resolved_at') - F('created_at')
    ).aggregate(
        avg_response=Avg('response_time')
    )['avg_response'] or timedelta(0)
    
    return {
        'average_response': avg_response,
        'ticket_count': resolved_tickets.count()
    }