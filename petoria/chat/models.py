from django.db import models
from users.models import User

class Chat(models.Model):
    """One-to-one private chat between exactly two users"""
    participants = models.ManyToManyField(User, through='ChatParticipant')
    pair_key = models.CharField(max_length=255, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    @staticmethod
    def make_pair_key(user1, user2):
        first, second = sorted([str(user1.id), str(user2.id)])
        return f"{first}:{second}"

    @classmethod
    def get_chat_between(cls, user1, user2):
        """Prevent duplicate chats between same users"""
        pair_key = cls.make_pair_key(user1, user2)
        chat = cls.objects.filter(pair_key=pair_key).first()
        if chat:
            return chat

        # Fallback for legacy rows without pair_key
        return (
            cls.objects.filter(participants=user1)
            .filter(participants=user2)
            .first()
        )

class ChatParticipant(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='participants_info')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    unread_count = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('chat', 'user')


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(default='content')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    reply_to = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="replies"
    )

    
    class Meta:
        ordering = ['-timestamp']
