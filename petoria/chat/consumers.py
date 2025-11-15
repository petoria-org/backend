import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from .models import Chat, Message
from .serializers import InChatMessageSerializer


class UserChatsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        await self.accept()

        # Subscribe to all chats
        self.chat_groups = [
            f"chat_{chat.id}" for chat in await self.get_user_chats()
        ]

        for group in self.chat_groups:
            await self.channel_layer.group_add(group, self.channel_name)

        await self.send(text_data=json.dumps({"status": "connected"}))

    async def disconnect(self, close_code):
        for group in self.chat_groups:
            await self.channel_layer.group_discard(group, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_body = data.get("message")
        chat_id = data.get("chat_id")

        if not message_body or not chat_id:
            return

        # Save message to DB
        message_obj = await self.save_message(chat_id, message_body)

        # Serialize
        serialized = InChatMessageSerializer(message_obj).data

        # Broadcast to the chat group
        await self.channel_layer.group_send(
            f"chat_{chat_id}",
            {
                "type": "chat_message",
                "message": serialized,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": event["message"]
        }))

    @database_sync_to_async
    def get_user_chats(self):
        return list(self.user.chats.all())

    @database_sync_to_async
    def save_message(self, chat_id, message_body):
        chat = Chat.objects.get(id=chat_id)
        return Message.objects.create(chat=chat, sender=self.user, body=message_body)