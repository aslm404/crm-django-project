from rest_framework import serializers
from .models import Conversation, Message
from team.serializers import UserSerializer
from clients.serializers import ClientSerializer

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'content', 'attachments',
            'timestamp', 'read'
        ]
        read_only_fields = ['sender', 'timestamp']

class ConversationSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_conversation_type_display', read_only=True)
    participants = UserSerializer(many=True, read_only=True)
    client = ClientSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'name', 'conversation_type', 'type_display', 'participants',
            'client', 'last_message', 'unread_count', 'created_at', 'updated_at'
        ]
    
    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return {
                'content': last_msg.content[:50],
                'timestamp': last_msg.timestamp,
                'sender': last_msg.sender.username
            }
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.exclude(sender=request.user).filter(read=False).count()
        return 0