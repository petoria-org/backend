from django.db import models
from users.models import User
from django.utils import timezone


class Chat (models.Model):
    User1 = models.ForeignKey(User,
                             on_delete = models.CASCADE,
                             related_name = 'chats_as_User1')

    User2 = models.ForeignKey(User,
                               on_delete = models.CASCADE,
                               related_name = 'chats_as_user2')

    message_ids = models.JSONField(default = list)
    created_at = models.DateTimeField(auto_now_add = True)

    class Meta:
        unique_together = ('User1', 'User2')

    def chat_name(self):
        return f"Chat-{self.id}"

    def participants(self):
        return [self.User1, self.User2]

    def __str__(self):
        return f"Chat between {self.User1} and {self.User2}"


































# from asgiref.sync import async_to_sync
# from channels.layers import get_channel_layer


class Chat(models.Model):
    participants = models.ManyToManyField(User, related_name='chats')
    post = models.ForeignKey(
        'posts.Post',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chats'
    )
    created_at = models.DateTimeField(default=timezone.now)

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
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    body = models.TextField('body')

    def __str__(self):
        return str(self.id)

    def characters(self):
        return len(self.body)
