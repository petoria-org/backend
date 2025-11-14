from rest_framework import serializers
from users.models import User
from users.serializers import BasicUserSerializer
from .models import Message

class MessageSerializer(
    serializers.ModelSerializer
):
    sender = BasicUserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'sender',
            'body',
            'timestamp'
        ]

class GetOrCreateChatSerializer(
    serializers.ModelSerializer
):
    model = User
    fields = ['id']