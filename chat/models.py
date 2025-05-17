from django.db import models
from team.models import TeamMember
from clients.models import Client
from support.models import SupportTicket

class Conversation(models.Model):
    CONVERSATION_TYPES = (
        ('team', 'Team'),
        ('client', 'Client'),
    )
    
    name = models.CharField(max_length=100, blank=True)
    participants = models.ManyToManyField(TeamMember, related_name='conversations')
    client = models.ForeignKey(Client, null=True, blank=True, on_delete=models.CASCADE)
    ticket = models.ForeignKey(SupportTicket, null=True, blank=True, on_delete=models.CASCADE)
    conversation_type = models.CharField(max_length=10, choices=CONVERSATION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.name:
            return self.name
        if self.client:
            return f"Client: {self.client.company}"
        participants = ", ".join(p.get_full_name() for p in self.participants.all())
        return f"Team: {participants or self.id}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(TeamMember, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    attachments = models.FileField(upload_to='message_attachments/', blank=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender}: {self.content[:20]}..."