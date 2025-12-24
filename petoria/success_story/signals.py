from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import SuccessStoryImage


@receiver(post_delete, sender=SuccessStoryImage)
def delete_success_story_image(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
