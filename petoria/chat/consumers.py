import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from .models import Chat, Message
from .serializers import InChatMessageSerializer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat_group_name = f"chat_{self.chat_id}"

        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )

        await self.accept()

        await self.send(text_data=json.dumps({"status": "connected"}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.chat_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_body = data.get("message")

        if not message_body:
            return

        # 1. Save to database
        message_obj = await self.save_message(message_body)

        # 2. Serialize the message for sending
        message_serialized = InChatMessageSerializer(message_obj).data

        # 3. Broadcast message to the chat window
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                "type": "chat_message",
                "message": message_serialized
            }
        )

        # 4. Broadcast update to chat list for ALL chat members
        await self.broadcast_chat_list_update(message_obj, message_serialized)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"]
        }))

    @database_sync_to_async
    def save_message(self, message_body):
        user = self.scope["user"]
        chat = Chat.objects.get(id=self.chat_id)
        return Message.objects.create(chat=chat, sender=user, body=message_body)

    @database_sync_to_async
    def get_chat_members(self):
        chat = Chat.objects.get(id=self.chat_id)
        return list(chat.members.all())

    async def broadcast_chat_list_update(self, message_obj, message_data):
        """
        Sends an event to each user's chatlist WebSocket:
        group name: user_{id}_chatlist
        """
        channel_layer = get_channel_layer()
        members = await self.get_chat_members()

        for user in members:
            await channel_layer.group_send(
                f"user_{user.id}_chatlist",
                {
                    "type": "chat_list_update",
                    "payload": {
                        "event": "chat_updated",
                        "chat_id": self.chat_id,
                        "last_message": message_data
                    }
                }
            )


class ChatListConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        self.group_name = f"user_{self.user.id}_chatlist"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def chat_list_update(self, event):
        """
        Called when ChatConsumer broadcasts an update.
        """
        await self.send(text_data=json.dumps(event["payload"]))
