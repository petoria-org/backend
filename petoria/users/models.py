from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill


class User(AbstractUser):
    
    # === Core Authentication Fields (from AbstractUser) ===
    # username - (150 chars, unique)
    # first_name - (150 chars)
    # last_name - (150 chars)  
    # password - (hashed)
    # is_active - (boolean)
    # is_staff - (boolean)
    # is_superuser - (boolean)
    # last_login - (datetime)
    # date_joined - (datetime)
    
    # === Contact/Notification Email ===
    email = models.EmailField(
        unique=True,
        error_messages={
            'unique': "This email is already registered. Please use a different email.",
        },
        help_text="Contact email for pet notifications and alerts"
    )
    
    phone = models.CharField(
        max_length=11,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^09[0-9]{9}$',
                message="Phone must start with 09 and contain 11 digits total."
            )
        ],
        help_text="Contact phone for urgent pet communications"
    )
    
    # === Profile Information ===
    profile_picture = ProcessedImageField(
        upload_to='profile_pics/',
        format='JPEG',
        options={'quality': 100},
        #processors=[ResizeToFill(300, 300)],
        null=True, 
        blank=True,
        default='profile_pics/default_avatar.png',
        help_text="User profile photo - helps build trust in the community"
    )
    
    bio = models.TextField(
        max_length=500, 
        blank=True,
        help_text="Brief introduction about yourself and your experience with pets"
    )

    # === Google Authentication ===
    google_id = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        unique=True,
        help_text="Google OAuth identifier for login"
    )
    
    # === Notification Preferences ===
    email_notifications = models.BooleanField(
        default=True,
        help_text="Receive email notifications about posts and messages"
    )
    
    def __str__(self):
        return f"{self.username}"

    @property
    def is_email_verified(self):
        """
        Check if user has any
        successful email verification
        """
        qs = self.email_verification
        return qs.filter(is_used=True).exists()
    
    @property
    def email_verified_at(self):
        """
        Get timestamp of 
        first successful verification
        """
        qs = self.email_verification
        successful = qs.filter(is_used=True).first()
        if successful:
            return successful.created_at
        return None
    
    @property
    def display_name(self):
        """
        Smart display name that prefers full name, falls back to username
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.username
    
    @property
    def has_contact_info(self):
        """
        Check if user has provided sufficient contact information
        """
        return bool(self.phone or self.is_email_verified)

class UserLocation(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='location'
    )
    point = models.PointField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class EmailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verification')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'is_used']),
        ]
    
    def __str__(self):
        return f"Verification for {self.user.email} - {self.created_at}"

    def is_expired(self):
        return timezone.now() > self.expires_at