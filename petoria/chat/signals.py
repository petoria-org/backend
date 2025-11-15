from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message

@receiver(post_save, sender=Message)
def update_chat_timestamp(sender, instance, created, **kwargs):
    if created:
        chat = instance.chat
        chat.updated_at = instance.timestamp
        chat.save(update_fields=['updated_at'])
