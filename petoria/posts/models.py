from django.db import models
from ckeditor.fields import RichTextField
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth.models import users  # custom user
from django.core.validators import RegexValidator, MinValueValidator
# from embed_video.fields import EmbedvideoField


class Post(models.Model):
    author = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE
        )
    
    title = models.CharField(max_length=80)
    
    description = RichTextField()
    
    award = models.IntegerField(  # Fixed: lowercase 'award' (Python convention)
        max_digits=12, 
        validators=[
            MinValueValidator(10000, message="Award must be at least 10000")
        ]
    )
    
    date_created = models.DateTimeField(auto_now_add=True)
    
    phone = models.CharField(
        max_length=11,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^09[0-9]{9}$',
                message="Phone must start with 09 and contain 11 digits total."
            )
        ]
    )
    
    # CONDITION = ()
    # state = models.ForeignKey('State', on_delete=models.PROTECT, null=False, related_name='posts')
    # category = models.ForeignKey('Category', on_delete=models.PROTECT, null=True, related_name='posts')
    # condition = models.CharField(max_length=100, choices=CONDITION)
    ### is_featured = models.BooleanField(default=False)


# class state(models.Model):
#     state_name = models.CharField(max_length=100)
#     slug = models.SlugField(blank=True, null=True)
#     def save(self, *args, **kwargs):
#         if not self.slug and self.state_name:
#             self.slug = slugify(self.state_name)
#         super().save(*args, **kwargs)


# class Category(models.Model):
#     pass

# class PostsImages(models.Model):
#     pass