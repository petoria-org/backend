from django.db import models
from cheditor.fields import RichTextField
from django.utils.text import slugify
from django.urls import reverse
from djando.contrib.auth.models import users  # custom user
# from embed_video.fields import EmbedvideoField
from django.core.validators import RegexValidator


class User(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(default='default-profile-pic.png', upload_to='upload/profile_pictures', null=True)
    phone = models.CharField(max_length=11, null=True, blank=True)  # Not mandatory.

    def __str__(self):
        return self.user.username


class Post(models.Model):
    # CONDITION = ()

    author = models.Foreignkey(Author, on_delete=models.CASCADE)
    title = models.CharField(max_length=180)
    description = RichTextField()
    Award = models.DecimalField(max_digits=8, decimal_places=2)  # 999,999.99
    date_created = DateTimeField(auto_now_add=True)
    state = models.ForeignKey('State', on_delete=models.PROTECT, null=False, related_name='ads')
    city = models.Foreignkey('City', on_delete=models.PROTECT, null=False, related_name='ads')
    category = models.ForeignKey('Category', on_delete=models.PROTECT, null=True, related_name='ads')
    # condition = models.CharField(max_length=100, choices=CONDITION)
    phone = models.CharField(max_length=50, validators=[
    RegexValidator(regex=r'^\+?\d{10,15}$', message="The contact number is not valid")])
    ### is_featured = models.BooleanField(default=False)


class state(models.Model):
    state_name = models.CharField(max_length=100)
    slug = models.SlugField(blank=True, null=True)
    def save(self, *args, **kwargs):
        if not self.slug and self.state_name:
            self.slug = slugify(self.state_name)
        super().save(*args, **kwargs)


class City(models.Model):


# ,,,

class Category(models.Model):


# ,,,

class AdsImages(models.Model):
# ,,,