# posts/models.py
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from locations.models import Location
from phonenumber_field.modelfields import PhoneNumberField
from users.models import User

from .enums import PetType, Gender, ContactMethod, PostStatus


class PostImage(models.Model):
    """
    Description: The storage model of advertisement images. Using the Generic Relations of each image
        It is connected to the relevant ad and the number of images per ad is limited to 7.
    """
    content_type: models.ForeignKey = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE
    )
    object_id: models.PositiveIntegerField = models.PositiveIntegerField()
    post: GenericForeignKey = GenericForeignKey("content_type", "object_id")
    image: models.ImageField = models.ImageField(upload_to="pets/")

    def clean(self):
        model_class = self.content_type.model_class()
        count = (
            model_class.objects.get(id=self.object_id).images.count()
            if self.object_id
            else 0
        )
        if count >= 7:
            raise ValidationError("Each post cannot have more than 7 photos.")

    thumbnail: ImageSpecField = ImageSpecField(source="image", processors=[ResizeToFill(300, 300)])


class BasePost(models.Model):
    """

    Editor: Mahshid Nourollah
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
        max_length=140,
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
        default=PetType.OTHER,
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

    pet_age = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Age of the pet.")
    )

    breed: models.CharField = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Breed (optional).")
    )

    Specific_symptoms: models.CharField = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Color or markings (optional).")
    )

    # === Location INFO ===
    location: models.OneToOneField = models.OneToOneField(
        Location,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='%(class)s'
    )

    # === CONTACT INFO ===
    contact_phone = PhoneNumberField(
        blank=True,
        null=True,
        help_text=_("Optional phone.")
    )
    contact_email = models.EmailField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Optional email")
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
        if self.color:
            parts.append(self.color.capitalize())
        if self.pet_sex:
            parts.append(self.pet_sex.capitalize())
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
        if isinstance(self, Lost_post):
            if not self.location or not (
                    self.location.point or self.location.city or self.location.country
            ):
                raise ValidationError(
                    "For lost pets, you must provide a location (coordinates or at least city/country)."
                )
        elif isinstance(self, (Found_post, Surrender_custody_pets)):
            if self.location and not (
                    self.location.point or self.location.city or self.location.country
            ):
                raise ValidationError(
                    "Location is incomplete. Provide city/country/coordinates or leave blank."
                )


class Found_post(BasePost):
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


class Lost_post(BasePost):
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


class Surrender_custody_pets(BasePost):
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

    # breed_size = models.CharField(
    # max_length=10,
    # choices=PetSIZES.choices,
    # default=PetSIZES.OTHER,
    # blank=True,
    # null=True,
    # help_text=_("Select the typical size of the breed(optional).")

    # )

    # health_status = models.CharField(
    # max_length=10,
    # choices=HealthStatus.choices,
    # default=HealthStatus.UNKNOWN,
    # blank=False,
    # null=False,
    # help_text=_("Select the current health condition of the pet.")
    # )

    # country_of_origin = models.CharField(
    # max_length=100,
    # blank=True,
    # null=True,
    # help_text=_("Enter the country where this breed is originally from (optional).")
    # )

    # suitable_for = models.CharField(
    # max_length=100,
    # choices=SUITABILITY.choices,
    # default=SUITABILITY.OTHER,
    # blank=True,
    # null=True,
    # help_text=_("Select what type of home this pet.")
    # )

    # average_lifespan = models.PositiveIntegerField(
    # blank=True,
    # null=True,
    # help_text=_("Enter the average lifespan of this breed in years (optional).")
    # )

# class Lost_post(BasePost):
# pass

# breed = models.CharField(
#     max_length=100,
#     blank=True,
#     help_text=_("Breed of the pet (leave blank if unknown)")
# )

# color = models.CharField(
#     max_length=100,
#     help_text=_("Color and distinctive markings")
# )

# # EXACT AGE - for owners who know precise age
# age = models.CharField(
#     max_length=50,
#     blank=True,
#     help_text=_("Exact age (e.g., '2 years 3 months', '8 months', '5 years')")
# )


# # EXACT AGE - for owners who know precise age
# age = models.CharField(
#     max_length=50,
#     blank=True,
#     help_text=_("Exact age (e.g., '2 years 3 months', '8 months', '5 years')")
# )


# images = models.JSONField(
#   default=list,
#    blank=True,
#   help_text=_("List of image URLs for the post")
# )
