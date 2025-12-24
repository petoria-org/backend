from django.urls import reverse
from rest_framework import serializers
from users.models import User
from .models import Chat, Message, ChatParticipant, Attachment
from .enums import AttachmentType


class AttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = [
            'id',
            'url',
            'download_url',
            'type',
            'content_type',
            'size',
            'created_at',
            'message',
        ]
        read_only_fields = ['id', 'url', 'type', 'content_type', 'size', 'created_at', 'message']

    def get_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url

    def get_download_url(self, obj):
        path = reverse("chat-attachment-download", args=[obj.id])
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(path)
        return path

class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(source='sender_id', read_only=True)
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    sender_profile_picture = serializers.SerializerMethodField()
    attachments = AttachmentSerializer(many=True, read_only=True)
    reply_to = serializers.SerializerMethodField()
    chat_id = serializers.IntegerField(source="chat_id", read_only=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'chat_id',
            'sender',
            'sender_id',
            'sender_name',
            'sender_profile_picture',
            'content',
            'reply_to',
            'attachments',
            'timestamp',
            'is_read',
        ]

    def get_sender_profile_picture(self, obj):
        try:
            if obj.sender.profile_picture:
                return obj.sender.profile_picture.url
        except Exception:
            pass
        return None

    def get_reply_to(self, obj):
        if not obj.reply_to:
            return None
        return {
            "id": obj.reply_to.id,
            "sender_id": obj.reply_to.sender_id,
            "sender_name": obj.reply_to.sender.username,
            "content": obj.reply_to.content,
        }


class UserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'profile_picture']

    def get_profile_picture(self, obj):
        try:
            if obj.profile_picture:
                return obj.profile_picture.url
        except Exception:
            pass
        return None

class ChatSerializer(serializers.ModelSerializer):
    other_participant = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message_time = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Chat
        fields = [
            'id',
            'other_participant',
            'last_message',
            'created_at',
            'unread_count',
            'last_message_time',
        ]

    # Returns the other person in the 1:1 chat
    def get_other_participant(self, obj):
        current_user = self.context['request'].user
        other = obj.participants.exclude(id=current_user.id).first()
        return UserSerializer(other).data if other else None

    # Returns the most recent message (messages are pre-ordered)
    def get_last_message(self, obj):
        # Prefer annotated fields from ChatListView to avoid extra queries
        if getattr(obj, "last_message_id", None):
            last_msg = (
                Message.objects
                .select_related("sender", "reply_to__sender")
                .prefetch_related("attachments")
                .filter(id=obj.last_message_id)
                .first()
            )
            if last_msg:
                return MessageSerializer(last_msg, context=self.context).data

        # Fallback for contexts without annotations
        last_msg = obj.messages.first()
        return MessageSerializer(last_msg).data if last_msg else None

    # Returns unread_count for the current user
    def get_unread_count(self, obj):
        user = self.context['request'].user
        try:
            participant = obj.participants_info.get(user=user)
            return participant.unread_count
        except ChatParticipant.DoesNotExist:
            return 0
