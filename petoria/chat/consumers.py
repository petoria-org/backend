import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist

from .models import Chat, Message, ChatParticipant, Attachment
from users.models import User
from django.urls import reverse
from django.db.models import F

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
            return

        self.user = self.scope["user"]
        self.inbox_group = f"user_{self.user.id}"

        # subscribe to inbox for chat list updates and notifications
        await self.channel_layer.group_add(self.inbox_group, self.channel_name)

        await self.accept()
        await self.send_json({"type": "connected"})


    async def disconnect(self, code):
        # Only discard inbox group if it was created
        if hasattr(self, "inbox_group"):
            await self.channel_layer.group_discard(self.inbox_group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try: data = json.loads(text_data)
        except: return await self.send_error("invalid_json")

        action = data.get("action")

        if action == "send_message":
            return await self.send_message_action(
                chat_id=data.get("chat_id"),
                recipient_id=data.get("recipient_id"),
                content=data.get("message"),
                reply_to_id=data.get("reply_to_id"),
                attachment_ids=data.get("attachment_ids")
            )

        if action == "mark_read":
            return await self.mark_as_read(
                data.get("chat_id"),
                data.get("message_ids", [])
            )

        return await self.send_error("unknown_action")

    # --------------------------------------------------------
    # ACTION: SEND MESSAGE (existing or new chat)
    # --------------------------------------------------------
    async def send_message_action(self, chat_id, recipient_id, content, reply_to_id, attachment_ids=None):
        
        # Validate content
        content = (content or "").strip()

        # Validate attachments
        attachment_ids = attachment_ids or []
        if not isinstance(attachment_ids, list):
            return await self.send_error("invalid_attachments")
        try:
            validated_attachment_ids = await self.validate_attachments(attachment_ids)
        except ValueError:
            return await self.send_error("invalid_attachments")

        # Check for empty message
        if not content and not attachment_ids:
            return await self.send_error("empty_message")


        # Getting a destination for the message:

        # Case 1: Existing chat
        if chat_id:
            if not await self.is_user_in_chat(chat_id):
                return await self.send_error("not_in_chat")

            if reply_to_id and not await self.is_message_in_chat(reply_to_id, chat_id):
                return await self.send_error("invalid_reply_target")

        # Case 2: First message → recipient_id
        elif recipient_id:
            try: recipient = await self.get_user(recipient_id)
            
            except ObjectDoesNotExist:
                return await self.send_error("recipient not found")
            
            if self.user == recipient:
                return await self.send_error("cant make a chat with yourself")
            
            chat = await self.get_or_create_chat(self.user, recipient)
            chat_id = chat.id

            if reply_to_id:
                return await self.send_error("invalid reply target")
        
        # Case 3 : No destination identifier was provided
        else:
            return await self.send_error("missing recipient_id and chat_id")
        
        # Creating new message
        try:
            msg = await self.create_message(
                chat_id,
                content,
                reply_to_id,
                validated_attachment_ids
            )
        except ValueError:
            return await self.send_error("invalid_attachments")
        except Exception:
            return await self.send_error("message_create_failed")
        
        serialized = await self.serialize_message(msg)


        # Realtime update to both users
        await self.broadcast_message_update(chat_id, serialized)

        return await self.send_json({
            "type": "message_sent",
            "chat_id": chat_id,
            "message": serialized
        })

    # --------------------------------------------------------
    # ACTION: MARK CHAT AS READ
    # --------------------------------------------------------
    async def mark_as_read(self, chat_id, message_ids):
        if not chat_id:
            return await self.send_error("missing_chat_id")
    
        if not await self.is_user_in_chat(chat_id):
            return await self.send_error("not_in_chat")
    
        if not message_ids:
            return await self.send_error("missing_message_ids")
    
        # mark specific messages
        updated_ids = await self.mark_specific_messages_as_read(
            chat_id, self.user.id, message_ids
        )
    
        await self.broadcast_read_update(chat_id, updated_ids)
        return await self.send_json({
            "type": "marked_read",
            "message_ids": updated_ids
        })


    # --------------------------------------------------------
    # CHANNEL LAYER HANDLERS
    # --------------------------------------------------------
    async def message_update(self, event):
        await self.send_json({"type": "message_update", "chat": event["chat"]})

    async def read_update(self, event):
        await self.send_json({"type": "read_update", "chat": event["chat"]})

    # --------------------------------------------------------
    # BROADCAST HELPERS
    # --------------------------------------------------------
    async def broadcast_message_update(self, chat_id, last_message):
        participants = await self.get_chat_participant_ids(chat_id)

        chat_preview = {
            "id": chat_id,
            "last_message": last_message,
        }

        for uid in participants:
            unread = await self.get_unread(uid, chat_id)
            chat_preview["unread_count"] = unread

            await self.channel_layer.group_send(
                f"user_{uid}",
                {
                    "type": "message_update",
                    "chat": chat_preview
                }
            )

    async def broadcast_read_update(self, chat_id, updated_ids):
        unread_count = await self.get_unread(self.user.id, chat_id)
        participants = await self.get_chat_participant_ids(chat_id)
        for uid in participants:
            update = {
                "id": chat_id,
                "reader_id": self.user.id,
                "unread_count": unread_count,
                "updated_ids": updated_ids
            }
            await self.channel_layer.group_send(
                f"user_{uid}",
                {
                    "type": "read_update",
                    "chat": update
                }
            )

    # --------------------------------------------------------
    # RESPONSE HELPERS
    # --------------------------------------------------------
    async def send_json(self, data):
        await self.send(text_data=json.dumps(data))

    async def send_error(self, msg):
        await self.send_json({"type": "error", "message": msg})


    # --------------------------------------------------------
    # DB HELPERS
    # --------------------------------------------------------
    @database_sync_to_async
    def mark_specific_messages_as_read(self, chat_id, user_id, message_ids):

        # Get the subset of provided IDs that are valid unread messages
        valid_ids = list(
            Message.objects.filter(
                chat_id=chat_id,
                id__in=message_ids,
                is_read=False
            )
            .exclude(sender_id=user_id)
            .values_list("id", flat=True)
        )

        if not valid_ids:
            return []

        # Mark them as read
        Message.objects.filter(id__in=valid_ids).update(is_read=True)

        # Decrease unread count efficiently
        ChatParticipant.objects.filter(
            chat_id=chat_id,
            user_id=user_id
        ).update(unread_count=F("unread_count") - len(valid_ids))

        return valid_ids


    @database_sync_to_async
    def get_user(self, user_id):
        return User.objects.get(id=user_id)

    @database_sync_to_async
    def is_user_in_chat(self, chat_id):
        return Chat.objects.filter(id=chat_id, participants=self.user).exists()

    @database_sync_to_async
    def get_or_create_chat(self, user1, user2):
        pair_key = Chat.make_pair_key(user1, user2)
        chat, created = Chat.objects.get_or_create(pair_key=pair_key)

        # ensure participants exist (idempotent for existing chats)
        ChatParticipant.objects.get_or_create(chat=chat, user=user1)
        ChatParticipant.objects.get_or_create(chat=chat, user=user2)

        return chat

    @database_sync_to_async
    def is_message_in_chat(self, message_id, chat_id):
        return Message.objects.filter(id=message_id, chat_id=chat_id).exists()

    @database_sync_to_async
    def create_message(self, chat_id, content, reply_to_id, attachment_ids=None):
        msg = Message.objects.create(
            chat_id=chat_id,
            sender=self.user,
            content=content,
            reply_to_id = reply_to_id
        )

        if attachment_ids:
            updated = Attachment.objects.filter(
                id__in=attachment_ids,
                uploaded_by=self.user,
                message__isnull=True,
            ).update(message=msg)

            if updated != len(attachment_ids):
                raise ValueError("Failed to bind attachments")

        # increment unread for OTHER participant
        ChatParticipant.objects.filter(chat_id=chat_id).exclude(user=self.user).update(
            unread_count=F("unread_count") + 1
        )

        return msg

    @database_sync_to_async
    def serialize_message(self, msg):
        attachments = [
            {
                "id": att.id,
                "url": att.file.url,
                "download_url": reverse("chat-attachment-download", args=[att.id]),
                "type": att.type,
                "content_type": att.content_type,
                "size": att.size,
            }
            for att in Attachment.objects.filter(message_id=msg.id)
        ]

        return {
            "id": msg.id,
            "chat_id": msg.chat.id,
            "sender_id": msg.sender.id,
            "sender_name": msg.sender.username,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "is_read": msg.is_read,
            "reply_to": (
                {
                    "id": msg.reply_to.id,
                    "sender_id": msg.reply_to.sender_id,
                    "sender_name": msg.reply_to.sender.username,
                    "content": msg.reply_to.content
                }
                if msg.reply_to else None
            ),
            "attachments": attachments,
        }

    @database_sync_to_async
    def validate_attachments(self, attachment_ids):
        if not attachment_ids:
            return []

        try:
            ids = [int(x) for x in attachment_ids]
        except (TypeError, ValueError):
            raise ValueError("invalid attachment ids")

        attachments = list(
            Attachment.objects.filter(
                id__in=ids,
                uploaded_by=self.user,
                message__isnull=True,
            ).values_list("id", flat=True)
        )

        if len(attachments) != len(ids):
            raise ValueError("some attachments invalid")

        return ids

    @database_sync_to_async
    def get_chat_participant_ids(self, chat_id):
        return list(Chat.objects.get(id=chat_id).participants.values_list("id", flat=True))

    @database_sync_to_async
    def get_unread(self, user_id, chat_id):
        try:
            return ChatParticipant.objects.get(user_id=user_id, chat_id=chat_id).unread_count
        except ChatParticipant.DoesNotExist:
            return 0
