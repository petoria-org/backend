from django.db import models
from users.models import User
from django.db.models import Count

class Chat(models.Model):
    """One-to-one private chat between exactly two users"""
    participants = models.ManyToManyField(User, through='ChatParticipant')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    @classmethod
    def get_chat_between(cls, user1, user2):
        """Prevent duplicate chats between same users"""
        return cls.objects.filter(
            participants=user1
        ).filter(
            participants=user2
        ).first()

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
    
    class Meta:
        ordering = ['-timestamp']