from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class User(AbstractUser):

    # should add a validation:    
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
    
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True, 
        null=True,
        validators=[
            # add file size/format validations
        ]
    )
    
    bio = models.TextField(max_length=500, blank=True)
    google_id = models.CharField(max_length=100, blank=True, null=True, unique=True)

    
    def __str__(self):
        return self.username
    
    @property
    def location(self):
        pass