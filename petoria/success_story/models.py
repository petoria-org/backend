# Create your models here.
# posts/models.py


from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User


class SuccessStory(models.Model):
    STORY_TYPE_CHOICES = [
        ('lost', 'Lost Pet'),
        ('found', 'Found Pet'),
        ('surrender', 'Surrender/Custody'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='success_stories'
    )
    title = models.CharField(
        max_length=100,
        blank=True
    )

    story = models.TextField(
        max_length=5000,
        help_text=_("شرح داستان موفقیت خود را بنویسید.")
    )
    story_type = models.CharField(
        max_length=20,
        choices=STORY_TYPE_CHOICES

    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.post_type} - {self.created_at.date()}"


