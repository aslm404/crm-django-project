import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Conversation, Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.conversation_group_name = f'chat_{self.conversation_id}'
        
        if not self.scope["user"].is_authenticated:
            await self.close()
            return
        
        if not await self.check_conversation_access():
            await self.close()
            return
        
        await self.update_user_presence(True)
        
        await self.channel_layer.group_add(
            self.conversation_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'user_activity',
                'user_id': self.scope["user"].id,
                'action': 'connected'
            }
        )
        
    @database_sync_to_async
    def check_conversation_access(self):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            user = self.scope["user"]
            
            if conversation.conversation_type == 'team':
                return user in conversation.participants.all()
            elif conversation.conversation_type == 'client':
                return user == conversation.client.user or user in conversation.participants.all()
            return False
        except Conversation.DoesNotExist:
            return False
        
    async def disconnect(self, close_code):
        if hasattr(self, 'conversation_group_name'):
            await self.update_user_presence(False)
            
            await self.channel_layer.group_discard(
                self.conversation_group_name,
                self.channel_name
            )
            
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'user_activity',
                    'user_id': self.scope["user"].id,
                    'action': 'disconnected'
                }
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'chat_message':
            await self.handle_chat_message(text_data_json)
        elif message_type == 'typing':
            await self.handle_typing_indicator(text_data_json)
        elif message_type == 'read_receipt':
            await self.handle_read_receipt(text_data_json)

    async def handle_chat_message(self, data):
        message = data['message']
        sender = self.scope["user"]
        
        message_obj = await self.save_message(message, sender)
        
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'chat_message',
                'message_id': message_obj.id,
                'sender_id': sender.id,
                'sender_name': sender.get_full_name(),
                'content': message,
                'timestamp': message_obj.timestamp.isoformat(),
            }
        )
    
    @database_sync_to_async
    def save_message(self, content, sender):
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=content
        )
        conversation.updated_at = message.timestamp
        conversation.save()
        return message

    async def handle_typing_indicator(self, data):
        is_typing = data['is_typing']
        
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.scope["user"].id,
                'user_name': self.scope["user"].get_full_name(),
                'is_typing': is_typing
            }
        )

    async def handle_read_receipt(self, data):
        message_id = data['message_id']
        
        await self.mark_message_as_read(message_id)
        
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'read_receipt',
                'message_id': message_id,
                'reader_id': self.scope["user"].id
            }
        )
    
    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        Message.objects.filter(
            id=message_id,
            conversation_id=self.conversation_id,
            read=False
        ).exclude(
            sender=self.scope["user"]
        ).update(read=True)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'content': event['content'],
            'timestamp': event['timestamp'],
            'is_me': event['sender_id'] == self.scope["user"].id
        }))
    
    async def typing_indicator(self, event):
        if event['user_id'] != self.scope["user"].id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing']
            }))
    
    async def read_receipt(self, event):
        if event['reader_id'] != self.scope["user"].id:
            await self.send(text_data=json.dumps({
                'type': 'read_receipt',
                'message_id': event['message_id'],
                'reader_id': event['reader_id']
            }))
    
    async def user_activity(self, event):
        if event['user_id'] != self.scope["user"].id:
            await self.send(text_data=json.dumps({
                'type': 'user_activity',
                'user_id': event['user_id'],
                'action': event['action']
            }))
    
    @database_sync_to_async
    def update_user_presence(self, is_online):
        user = self.scope["user"]
        user.is_online = is_online
        user.save()