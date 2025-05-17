from django.db import models
from clients.models import Client
from team.models import TeamMember
import uuid

class TicketCategory(models.Model):
    NAME_CHOICES = (
        ('technical_support', 'Technical Support'),
        ('billing_issue', 'Billing Issue'),
        ('account_management', 'Account Management'),
        ('feature_request', 'Feature Request'),
        ('bug_report', 'Bug Report'),
        ('general_inquiry', 'General Inquiry'),
    )
    
    name = models.CharField(max_length=100, choices=NAME_CHOICES)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.get_name_display()

class SupportTicket(models.Model):
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    
    ticket_number = models.CharField(max_length=20, unique=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(TicketCategory, on_delete=models.SET_NULL, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    assigned_to = models.ForeignKey(TeamMember, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(TeamMember, on_delete=models.CASCADE, related_name='created_tickets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.ticket_number} - {self.subject}"

class TicketComment(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(TeamMember, on_delete=models.CASCADE)
    content = models.TextField()
    attachments = models.FileField(upload_to='ticket_attachments/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_internal = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author} on {self.ticket}"

class TicketStatusUpdate(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='status_updates')
    changed_by = models.ForeignKey(TeamMember, on_delete=models.CASCADE)
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"Status changed from {self.old_status} to {self.new_status}"