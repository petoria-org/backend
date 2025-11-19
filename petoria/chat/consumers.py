import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import PermissionDenied
from django.db.models import F
from users.models import User
from .models import Chat, Message, ChatParticipant

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope['user'].is_anonymous:
            await self.close()
            return
        
        self.user = self.scope['user']
        self.user_channel_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.user_channel_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'active_chat_id'):
            await self.channel_layer.group_discard(f"chat_{self.active_chat_id}", self.channel_name)
        await self.channel_layer.group_discard(self.user_channel_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data['action']
            
            if action == 'join_chat':
                await self.handle_join_chat(data['chat_id'])
            elif action == 'send_message':
                await self.handle_send_message(data['chat_id'], data['message'])
            elif action == 'mark_read':
                await self.handle_mark_read(data['chat_id'])
            else:
                await self.send_error(f"Unknown action: {action}")
                
        except (json.JSONDecodeError, KeyError) as e:
            await self.send_error(f"Invalid request: {e}")

    async def handle_join_chat(self, chat_id):
        try:
            if not await self.is_user_in_chat(chat_id):
                raise PermissionDenied("Access denied")
            
            if hasattr(self, 'active_chat_id'):
                await self.channel_layer.group_discard(f"chat_{self.active_chat_id}", self.channel_name)
            
            self.active_chat_id = chat_id
            await self.channel_layer.group_add(f"chat_{chat_id}", self.channel_name)
            await self.send(json.dumps({'type': 'chat_joined', 'chat_id': chat_id}))
            
        except PermissionDenied as e:
            await self.send_error(str(e))

    async def handle_send_message(self, chat_id, message_text):
        try:
            if not await self.is_user_in_chat(chat_id):
                raise PermissionDenied("Cannot send message to this chat")
            
            if not message_text or len(message_text.strip()) == 0:
                raise ValueError("Message cannot be empty")
            
            if len(message_text) > 5000:
                raise ValueError("Message too long")
            
            message = await self.save_message(chat_id, message_text)
            
            await self.channel_layer.group_send(
                f"chat_{chat_id}",
                {'type': 'chat_message', 'message': message}
            )
            
            participants = await self.get_chat_participants(chat_id)
            for participant_id in participants:
                unread = await self.get_unread_count(chat_id, participant_id)
                await self.channel_layer.group_send(
                    f"user_{participant_id}",
                    {
                        'type': 'chat_list_update',
                        'chat': {
                            'id': chat_id,
                            'last_message': {
                                'id': message['id'],
                                'sender_id': message['sender_id'],
                                'sender_name': message['sender_name'],
                                'content': message['content'][:150],
                                'timestamp': message['timestamp']
                            },
                            'unread_count': unread
                        }
                    }
                )
            
            await self.increment_unread_counts(chat_id)
            
        except (PermissionDenied, ValueError) as e:
            await self.send_error(str(e))

    async def handle_mark_read(self, chat_id):
        try:
            if not await self.is_user_in_chat(chat_id):
                raise PermissionDenied("Access denied")
            
            read_info = await self.mark_messages_as_read(chat_id)
            
            if read_info['message_ids']:
                await self.channel_layer.group_send(
                    f"chat_{chat_id}",
                    {
                        'type': 'read_receipt',
                        'reader_id': self.user.id,
                        'reader_name': self.user.username,
                        'message_ids': read_info['message_ids']
                    }
                )
            
        except PermissionDenied as e:
            await self.send_error(str(e))

    @database_sync_to_async
    def is_user_in_chat(self, chat_id):
        return Chat.objects.filter(id=chat_id, participants=self.user).exists()

    @database_sync_to_async
    def save_message(self, chat_id, content):
        chat = Chat.objects.get(id=chat_id)
        message = Message.objects.create(chat=chat, sender=self.user, content=content)
        return {
            'id': message.id,
            'chat_id': chat_id,
            'sender_id': self.user.id,
            'sender_name': self.user.username,
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
            'is_read': message.is_read
        }

    @database_sync_to_async
    def get_chat_participants(self, chat_id):
        return list(Chat.objects.get(id=chat_id).participants.values_list('id', flat=True))

    @database_sync_to_async
    def get_unread_count(self, chat_id, user_id):
        try:
            participant = ChatParticipant.objects.get(chat_id=chat_id, user_id=user_id)
            return participant.unread_count
        except ChatParticipant.DoesNotExist:
            return 0

    @database_sync_to_async
    def increment_unread_counts(self, chat_id):
        ChatParticipant.objects.filter(
            chat_id=chat_id
        ).exclude(user=self.user).update(
            unread_count=F('unread_count') + 1
        )

    @database_sync_to_async
    def mark_messages_as_read(self, chat_id):
        message_ids = list(Message.objects.filter(
            chat_id=chat_id,
            is_read=False
        ).exclude(sender=self.user).values_list('id', flat=True))
        
        Message.objects.filter(id__in=message_ids).update(is_read=True)
        ChatParticipant.objects.filter(
            chat_id=chat_id,
            user=self.user
        ).update(unread_count=0)
        
        return {'message_ids': message_ids}

    async def chat_message(self, event):
        await self.send(json.dumps({'type': 'new_message', 'message': event['message']}))

    async def read_receipt(self, event):
        await self.send(json.dumps({
            'type': 'read_receipt',
            'reader_id': event['reader_id'],
            'reader_name': event['reader_name'],
            'message_ids': event['message_ids']
        }))

    async def new_chat_notification(self, event):
        await self.send(json.dumps({'type': 'new_chat_available', 'chat': event['chat']}))

    async def chat_list_update(self, event):
        await self.send(json.dumps({
            'type': 'chat_list_update',
            'chat': event['chat']
        }))

    async def send_error(self, message):
        await self.send(json.dumps({'type': 'error', 'message': message}))