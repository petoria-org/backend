from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import LostPost, FoundPost, SurrenderCustodyPet


def _delete_images_for_post(instance):
    images = getattr(instance, "images", None)
    if not images:
        return
    for img in images.all():
        # Delete file from storage then remove db row
        img.image.delete(save=False)
        img.delete()


@receiver(post_delete, sender=LostPost)
def delete_lost_post_images(sender, instance, **kwargs):
    _delete_images_for_post(instance)


@receiver(post_delete, sender=FoundPost)
def delete_found_post_images(sender, instance, **kwargs):
    _delete_images_for_post(instance)


@receiver(post_delete, sender=SurrenderCustodyPet)
def delete_custody_post_images(sender, instance, **kwargs):
    _delete_images_for_post(instance)
