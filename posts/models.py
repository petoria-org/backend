# posts/models.py
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.utils.translation import gettext_lazy as _
from locations.models import Location
from users.models import User

from .enums import PetType, Gender, ContactMethod, PostStatus


class PostImage(models.Model):
    """
    Description: The storage model of advertisement images. Using the Generic Relations of each image
        It is connected to the relevant ad and the number of images per ad is limited to 7.
    """
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="post_images",
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    post = GenericForeignKey("content_type", "object_id")
    image = models.ImageField(upload_to="posts/")
    created_at = models.DateTimeField(auto_now_add=True)


class PetAge(models.Model):
    years = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        help_text=_("Age of the pet in years.")
    )

    months = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(11)],
        help_text=_("Additional months of age (0-11).")
    )

    def clean(self):
        if self.years is None and self.months is None:
            raise ValidationError("Provide years or months for pet age.")

    @property
    def display(self):
        parts = []
        if self.years is not None:
            parts.append(f"{self.years} سال")
        if self.months is not None:
            parts.append(f"{self.months} ماه")
        return " و ".join(parts)

    def __str__(self):
        return self.display or "unknown"



class BasePost(models.Model):
    """

    Description: Abstract base model for all post types (lost, found, surrender/adoption).

    includes:
    - Core post fields (title, description, user)
    - Pet information (type, sex, name, breed, color)
    - Location (optional for some posts, required for Lost posts)
    - Contact information (phone, email)
    - Images (GenericRelation)
    - Status handling and utility methods

    Notes:
    - This model is abstract .
    - Child classes add their own specific fields.
    """

    # === CORE POST INFO ===
    title: models.CharField = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        help_text=_("Clear, descriptive title for the post")
    )

    description: models.TextField = models.TextField(
        max_length=5000,
        blank=True,
        help_text=_("Detailed description of the pet and situation")
    )

    user: models.ForeignKey = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)ss'
    )

    # === PET INFO ===
    pet_type: models.CharField = models.CharField(
        max_length=20,
        choices=PetType.choices,
        default=PetType.OTHERS,
        blank=False,
        null=False,
        help_text=_("Select the type of pet.")
    )

    pet_sex: models.CharField = models.CharField(
        max_length=10,
        choices=Gender.choices,
        default=Gender.UNKNOWN,
        blank=False,
        null=False,
        help_text=_("Select the gender of the pet.")
    )

    pet_name: models.CharField = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Pet's name (optional).")
    )

    pet_age = models.OneToOneField(
        PetAge,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
        help_text=_("Age of the pet.")
    )

    breed = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Breed (optional).")
    )

    Specific_symptoms = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Color or markings (optional).")
    )

    # === Location INFO ===
    location = models.OneToOneField(
        Location,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='%(class)s'
    )

    # === CONTACT INFO ===

    contact_phone = models.BooleanField(
        default=False,
        help_text=_("Show phone")
    )

    contact_email = models.BooleanField(
        default=False,
        help_text=_("Show email ")
    )

    # === STATUS & METADATA ===
    status = models.CharField(
        max_length=20,
        choices=PostStatus.choices,
        default=PostStatus.ACTIVE,
        help_text=_("Select the current status of the post.")
    )

    images = GenericRelation(
        PostImage,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    """Automatically generates a fallback title based on pet info."""

    def generate_auto_title(self):
        parts: list[str] = [self.pet_type.capitalize()]
        if self.pet_type:
            parts.append(self.pet_type.capitalize())
        if self.location and self.location.city:
            parts.append(f"near {self.location.city}")
        return " ".join(parts).strip()

    def save(self, *args, **kwargs):
        if not self.title or self.title.strip() == "":
            self.title = self.generate_auto_title()
        super().save(*args, **kwargs)

    def is_active(self):
        return self.status == PostStatus.ACTIVE

    def mark_as_resolved(self):
        self.status = PostStatus.RESOLVED
        self.save()

    def get_available_contact_methods(self):
        methods: list[ContactMethod] = [ContactMethod.CHAT]
        if self.contact_phone:
            methods.append(ContactMethod.PHONE)
        if self.contact_email:
            methods.append(ContactMethod.EMAIL)
        return methods

    def clean(self):
        #  location validation
        if isinstance(self, LostPost):
            if not self.location or not (
                    (
                        self.location.latitude is not None
                        and self.location.longitude is not None
                    )
                    or self.location.city
                    or self.location.country
            ):
                raise ValidationError(
                    "For lost pets, you must provide a location (coordinates or at least city/country)."
                )
        elif isinstance(self, (FoundPost, SurrenderCustodyPet)):
            if self.location and not (
                    (
                        self.location.latitude is not None
                        and self.location.longitude is not None
                    )
                    or self.location.city
                    or self.location.country
            ):
                raise ValidationError(
                    "Location is incomplete. Provide city/country/coordinates or leave blank."
                )


class FoundPost(BasePost):
    """
    Represents a found-pet report.

    Inherits all common fields from BasePost.
    Adds:
        - found_time: When the pet was found.
    """
    found_time: models.DateTimeField = models.DateTimeField(
        blank=True,
        null=True,
        help_text=_("When the pet was found.")
    )


class LostPost(BasePost):
    """
    Represents a lost-pet report.

    Inherits all common fields from BasePost.
    Adds:
        - lost_time: When the pet was lost.
     """
    lost_time: models.DateTimeField = models.DateTimeField(
        blank=True,
        null=True,
        help_text=_("When the pet was lost.")
    )


class SurrenderCustodyPet(BasePost):
    """
    Represents a pet being surrendered or offered for adoption.

    Additional fields include:
        - diseases
        - has_birth_certificate
        - vaccination
        - steriliz
    """

    diseases: models.TextField = models.TextField(
        blank=True,
        help_text=_("Known diseases or health issues.")
    )

    has_birth_certificate: models.BooleanField = models.BooleanField(
        default=False,
        help_text=_("Does the pet have a birth certificate?")
    )

    vaccination: models.BooleanField = models.BooleanField(default=False)

    steriliz: models.BooleanField = models.BooleanField(default=False)
