from django.db import models
from users.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError

class Chat(models.Model):
    members = models.ManyToManyField(User, related_name='chats')
    is_private = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Chat {self.id}"

    def add_member(self, user):
        if self.is_private and self.members.count() >= 2:
            raise ValidationError(
                "Private chats cannot" \
                " have more than 2 participants."
            )
        self.members.add(user)

    def add_members(self, *users):
        for user in users:
            self.add_member(user)


    @staticmethod
    def get_or_create_private_chat(user1, user2):
        """
        Return the existing chat between these two users OR create a new one.
        """
        chat = Chat.objects.filter(
            is_private=True,
            members=user1
        ).filter(
            members=user2
        ).first()

        if not chat:
            chat = Chat.objects.create(is_private=True)
            chat.add_members(user1, user2)
        return chat


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    body = models.TextField(null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return str(self.id)