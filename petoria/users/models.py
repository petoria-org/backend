import random
from datetime import timedelta
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models
from django.utils import timezone
from locations.models import Location
from phonenumber_field.modelfields import PhoneNumberField


def user_avatar_path(instance, filename):
    ext = filename.split(".")[-1] if "." in filename else ""
    # Use user id to shard; fall back to tmp until the user is saved
    user_id = instance.id or "tmp"
    suffix = f".{ext}" if ext else ""
    return f"profile_pics/{user_id}/{uuid4().hex}{suffix}"


class User(AbstractUser):
    """"
     Core Authentication Fields (from AbstractUser)
    - password - (hashed)
    - is_active - (boolean)
    - is_staff - (boolean)
    - is_superuser - (boolean)
    - last_login - (datetime)
    - date_joined - (datetime)

    Login with username or email.
    Email verification required to activate account.
    """
    first_name = models.CharField(
        max_length=30,
    )
    last_name = models.CharField(
        max_length=30,
    )
    username = models.CharField(
        max_length=50,
        unique=True      
    )
    # === Contact/Notification Email ===
    email = models.EmailField(
        unique=True,
        error_messages={
            'unique': "This email is already registered. Please use a different email.",
        },
        help_text="Contact email for pet notifications and alerts"
    )

    phone = PhoneNumberField(
        blank=True,
        null=True,
        help_text="Contact phone for urgent pet communications"
    )

    # === Profile Information ===

    profile_picture = models.ImageField(
        upload_to=user_avatar_path,
        null=True,
        blank=True,
        default='profile_pics/default_avatar.png',
        help_text="User profile photo"
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
        help_text="Receive email notifications "
    )

    # === Location ===
    location = models.OneToOneField(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user'
    )

    is_email_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username}"

    def email_verified_at(self):
        """
        Get timestamp of first successful verification
        """
        qs = self.email_verification
        successful = qs.filter(is_used=True).first()
        if successful:
            return successful.created_at
        return None

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
        self.user.is_email_verified = True
        # Mark email as verified on the user model
        self.user.email = self.email
        self.user.is_email_verified = True
        self.user.save()

    def __str__(self):
        return f"Code {self.code} for {self.email}"
