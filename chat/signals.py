from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Message)
def send_message_notification(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        conversation = instance.conversation
        group_name = f"chat_{conversation.id}"
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "chat_message",
                "message_id": instance.id,
                "sender_id": instance.sender.id,
                "sender_name": instance.sender.get_full_name(),
                "content": instance.content,
                "timestamp": instance.timestamp.isoformat(),
            }
        )
        
        logger.info(f"Sent real-time notification for message {instance.id} in conversation {conversation.id}")