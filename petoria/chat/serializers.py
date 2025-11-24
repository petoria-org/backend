from rest_framework import serializers
from users.models import User
from .models import Chat, Message, ChatParticipant

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'sender',
            'sender_name',
            'content',
            'timestamp',
            'is_read',
        ]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

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