from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from locations.models import Location
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill
import random
from datetime import timedelta


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
    

    # === Location ===
    location = models.OneToOneField(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user'
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



def generate_6_digit_code():
    return f"{random.randint(100000, 999999)}"

class EmailVerification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="email_verification_codes"
    )

    email = models.EmailField(null=True)
    code = models.CharField(max_length=6, default=generate_6_digit_code)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Automatically set expiration time (2 minutes default)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=2)
        super().save(*args, **kwargs)

    def is_valid(self):
        """Return True if code is not used and not expired."""
        now = timezone.now()
        return (not self.is_used) and (now <= self.expires_at)

    def mark_used(self):
        """Mark this code as used and verify the user."""
        self.is_used = True
        self.save()

        # Mark email as verified on the user model
        self.user.email = self.email
        self.user.is_email_verified = True
        self.user.save()

    def __str__(self):
        return f"Code {self.code} for {self.email}"