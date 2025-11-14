from rest_framework import serializers
from users.models import User
from .models import Message

class MessageSerializer(
    serializers.ModelSerializer
):
    sender = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id',
            'sender',
            'body',
            'timestamp'
        ]

    def get_sender(self, obj):
        user = obj.sender
        pfp = None
        if user.profile_picture.url:
            pfp = user.profile_picture.url
        return {
            "id": user.id,
            "username": user.username,
            "profile_picture": pfp,
        }

class GetOrCreateChatSerializer(
    serializers.ModelSerializer
):
    model = User
    fields = ['id']