from rest_framework import serializers
from users.models import User
from .models import Chat, Message, ChatParticipant

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_name', 'content', 'timestamp', 'is_read']

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
        fields = ['id', 'other_participant', 'last_message', 'created_at', 'unread_count', 'last_message_time']
    
    def get_other_participant(self, obj):
        current_user = self.context['request'].user
        other_user = obj.participants.exclude(id=current_user.id).first()
        return UserSerializer(other_user).data if other_user else None
    
    def get_last_message(self, obj):
        last_msg = obj.messages.first()
        return MessageSerializer(last_msg).data if last_msg else None
    
    def get_unread_count(self, obj):
        try:
            participant = obj.participants_info.get(user=self.context['request'].user)
            return participant.unread_count
        except ChatParticipant.DoesNotExist:
            return 0

class CreateChatSerializer(serializers.Serializer):
    other_user_id = serializers.IntegerField()
    message = serializers.CharField(max_length=5000)
    
    def validate_other_user_id(self, value):
        if value == self.context['request'].user.id:
            raise serializers.ValidationError("Cannot chat with yourself")
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        return value