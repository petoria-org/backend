from django.db import models
from users.models import User
from django.utils import timezone


class Chat(models.Model):
    # post = models.ForeignKey(
    #     'posts.Post',
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name='chats'
    # )
    participants = models.ManyToManyField(User, related_name='chats')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Chat {self.id} about Post {self.post_id if self.post else 'N/A'}"

    def is_private(self):
        """Return True if chat has exactly two participants."""
        return self.participants.count() == 2
    

class Message(models.Model):
    
    """
       This class represents a chat message. It has a owner (user), timestamp and
       the message body.
    """
        
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField(null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return str(self.id)