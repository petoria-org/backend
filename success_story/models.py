from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User
from posts.enums import PetType


class SuccessStory(models.Model):
    STORY_TYPE_CHOICES = [
        ('lost', 'Lost Pet'),
        ('found', 'Found Pet'),
        ('surrender', 'Surrender/Custody'),
    ]

    title = models.CharField(
        max_length=100,
        blank=True
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='success_stories'
    )

    story = models.TextField(
        max_length=1000
    )
    
    story_type = models.CharField(
        max_length=20,
        choices=STORY_TYPE_CHOICES

    )

    pet_type = models.CharField(
        max_length=20,
        choices=PetType.choices,
        default=PetType.OTHERS,
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # image
    def __str__(self):
        return f"{self.user.username} - {self.story_type} - {self.created_at.date()}"


class SuccessStoryImage(models.Model):
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="success_story_images",
    )
    success_story = models.ForeignKey(
        SuccessStory,
        on_delete=models.CASCADE,
        related_name="images",
        null=True,
        blank=True,
    )
    image = models.ImageField(upload_to="success_stories/")
    created_at = models.DateTimeField(auto_now_add=True)
