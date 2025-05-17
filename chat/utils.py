from django.db.models import Q
from datetime import datetime
from .models import Conversation, Message

def get_unread_message_count(user):
    return Message.objects.filter(
        conversation__participants=user,
        read=False
    ).exclude(
        sender=user
    ).count()

def get_user_conversations(user):
    conversations = Conversation.objects.filter(
        Q(participants=user) | Q(client__user=user)
    ).distinct()
    
    result = []
    for conv in conversations:
        last_message = conv.messages.order_by('-timestamp').first()
        unread = conv.messages.filter(read=False).exclude(sender=user).count()
        
        result.append({
            'id': conv.id,
            'name': conv.name or conv.client.company if conv.client else "Group Chat",
            'last_message': last_message.content[:50] if last_message else None,
            'timestamp': last_message.timestamp if last_message else conv.created_at,
            'unread_count': unread,
            'type': conv.conversation_type
        })
    
    result.sort(key=lambda x: x['timestamp'], reverse=True)
    return result

def mark_conversation_read(conversation, user):
    conversation.messages.exclude(sender=user).update(read=True)