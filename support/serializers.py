from rest_framework import serializers
from .models import TicketCategory, SupportTicket, TicketComment
from clients.serializers import ClientSerializer
from team.serializers import UserSerializer

class TicketCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketCategory
        fields = ['id', 'name', 'description']

class SupportTicketSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    client = ClientSerializer(read_only=True)
    category = TicketCategorySerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = SupportTicket
        fields = [
            'id', 'ticket_number', 'client', 'subject', 'description',
            'category', 'priority', 'priority_display', 'status', 'status_display',
            'assigned_to', 'created_by', 'created_at', 'updated_at', 'resolved_at'
        ]
        read_only_fields = ['ticket_number', 'created_by']

class TicketCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = TicketComment
        fields = ['id', 'ticket', 'author', 'content', 'attachments', 'is_internal', 'created_at']
        read_only_fields = ['author', 'created_at']
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)