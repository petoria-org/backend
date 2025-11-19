# posts/models.py
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from phonenumber_field.modelfields import PhoneNumberField
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

from users.models import User
from locations.models import Location
from .enums import PetType, Gender, ContactMethod, PostStatus, HealthStatus, Pet_SIZES, SUITABILITY



class PostImage(models.Model):

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    post = GenericForeignKey('content_type', 'object_id')

    image = models.ImageField(upload_to='pets/')

    def clean(self):
        model_class = self.content_type.model_class()
        count = model_class.objects.get(id=self.object_id).images.count() if self.object_id else 0
        if count >= 7:
            raise ValidationError("Each post cannot have more than 7 photos.")

    thumbnail = ImageSpecField(
        source='image',
        processors=[ResizeToFill(300, 300)]
    )


class BasePost(models.Model):

    # === CORE POST INFO ===
    title = models.CharField(
        max_length = 140,
        help_text = _("Clear, descriptive title for the post"),
        blank = False,
        null = False,
    )
    
    description = models.TextField(
        max_length = 5000,
        blank = True,
        null = False,
        help_text = _("Detailed description of the pet and situation")
    )

    user = models.ForeignKey(
        User,
        on_delete = models.CASCADE,
        related_name = '%(class)ss'
    )

    # === PET INFO ===
    pet_type = models.CharField(
        max_length = 20,
        choices = PetType.choices,
        default = PetType.OTHER,
        blank = False,
        null = False,
        help_text = _("Select the type of pet.")
    )

    pet_sex = models.CharField(
        max_length = 10,
        choices = Gender.choices,
        default = Gender.UNKNOWN,
        blank = False,
        null = False,
        help_text = _("Select the gender of the pet.")
    )

    pet_name = models.CharField(
        max_length = 100,
        blank = True,
        help_text = _("Enter the pet's name if known (optional).")
    )

    breed = models.CharField(
        max_length = 100,
        blank = True,
        help_text = _("Specify the breed of the pet (optional).")
    )

    color = models.CharField(
        max_length=100,
        blank = True,
        help_text = _("Describe color and distinctive markings of the pet (optional).")
    )

    # === Location info ===
    location = models.OneToOneField(
        Location,
        on_delete=models.SET_NULL,
        blank = True,
        null = True,
        related_name='%(class)s'
    )

    # === CONTACT INFO ===
    contact_phone = PhoneNumberField(
        blank = True,
        null = True,
        help_text = _("Enter a phone number in international format (optional).")
    )

    contact_email = models.EmailField(
        max_length = 100,
        blank = True,
        null = True,
        help_text = _("Enter an email address for direct contact (optional).")
    )

    # === STATUS & METADATA ===
    status = models.CharField(
        max_length = 20,
        choices = PostStatus.choices,
        default = PostStatus.ACTIVE,
        blank=False,
        null=False,
        help_text = _("Select the current status of the post.")
    )

    # === PICTURES ===
    images = GenericRelation(
        PostImage,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

     class Meta:
            abstract = True
            ordering = ['-created_at']

    def generate_auto_title(self):
        parts = [self.pet_type.capitalize()]
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
        methods = [ContactMethod.CHAT]
        if self.contact_phone:
            methods.append(ContactMethod.PHONE)
        if self.contact_email:
            methods.append(ContactMethod.EMAIL)
        return methods

    def clean(self):
        #  location validation
        if isinstance(self, Lost_post):
            if not self.location or not (self.location.point or self.location.city or self.location.country):
                raise ValidationError("For lost pets, you must provide a location (coordinates or at least city/country).")
        elif isinstance(self, (Found_post, Surrender_custody_pets)):
            if self.location and not (self.location.point or self.location.city or self.location.country):
                raise ValidationError("Location is incomplete. Provide city/country/coordinates or leave blank.")





class Surrender_custody_pets(BasePost):

    health_status = models.CharField(
        max_length = 10,
        choices = HealthStatus.choices,
        default = HealthStatus.UNKNOWN,
        blank = False,
        null = False,
        help_text = _("Select the current health condition of the pet.")
    )

    country_of_origin = models.CharField(
        max_length = 100,
        blank = True,
        null = True,
        help_text = _("Enter the country where this breed is originally from (optional).")
    )

    suitable_for = models.CharField(
        max_length=100,
        choices=SUITABILITY_CHOICES,
        default= SUITABILITY.UNKNOWN,
        blank = True,
        null = True,
        help_text=_("Select what type of home this pet.")
        )

    average_lifespan = models.PositiveIntegerField(
        blank = True,
        null = True,
        help_text = _("Enter the average lifespan of this breed in years (optional).")
    )

    breed_size = models.CharField(
        max_length=10,
        choices=Pet_SIZES.choices,
        default=Pet_SIZES.UNKNOWN,
        blank = True,
        null = True,
        help_text=_("Select the typical size of the breed(optional).")

    )

class Found_post(BasePost):
    pass
class Lost_post(BasePost):
    pass





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
    #)


'''
to do list:


Base Post:

1) decide if lost and found should be separate

2) find how to get location

3) suggest default phone number and email to user when creating post objects
   + make sure they can set it to null

4) create lost, found, adopt posts

5) make a default for title (probably in save method)

'''
