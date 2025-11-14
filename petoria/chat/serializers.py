from users.models import User
from users.serializers import BasicUserSerializer
from .models import Message, Chat

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer




class GetOrCreateChatSerializer(ModelSerializer):
    model = User
    fields = ['id']


class MessageSerializer(ModelSerializer):
    sender = BasicUserSerializer(read_only=True)
    class Meta:
        model = Message
        fields = [
            'id',
            'sender',
            'body',
            'timestamp'
        ]


class ChatListSerializer(ModelSerializer):
    members = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = [
            'id',
            'members',
            'last_message',
            'unread_count'
        ]
    
    def get_members(self, obj):
        request = self.context.get('request')
        if not request:
            return []
        user_id = request.user.id

        return [
            BasicUserSerializer(
                user,
                context=self.context
            ).data
            for user in obj.members.exclude(id=user_id)
        ]

    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return MessageSerializer(
                last_msg,
                context=self.context,
            ).data
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request:
            return 0
        return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
    