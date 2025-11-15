# posts/models.py
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.core.exceptions import ValidationError
from users.models import User
from locations.models import Location
from .enums import PetType, Gender, ContactMethod, PostStatus


'''
to do list:


Base Post:

1) decide if lost and found should be separate

2) make image verifications (size, format, ....)

3) find how to get location

4) suggest default phone number and email to user when creating post objects
   + make sure they can set it to null 

5) create lost, found, adopt posts

6) make a default for title (probably in save method)

'''


class BasePost(models.Model):

    # === CORE POST INFORMATION ===
    title = models.CharField(
        max_length=140,
        help_text=_("Clear, descriptive title for the post")
    )
    
    description = models.TextField(
        max_length=5000,
        blank=True,
        help_text=_("Detailed description of the pet and situation")
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)ss'
    )

    # === MEDIA ===
   # images = models.JSONField(
    #   default=list,
    #    blank=True,
     #   help_text=_("List of image URLs for the post")
    #)

    # === Location info ===
    location = models.OneToOneField(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s'
    )

    # === PET IDENTIFICATION ===
    pet_type = models.CharField(
        max_length=20,
        choices=PetType.choices,
        default= PetType.OTHER,
        help_text=_("Type of pet")
    )

    pet_sex = models.CharField(
        max_length=10,
        choices=Gender.choices,
        default=Gender.UNKNOWN,
        help_text=_("Gender of the pet")
    )

    pet_name = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Name of the pet (if known)")
    )

    # === CONTACT ===
    contact_phone = models.CharField(
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
    contact_email = models.EmailField(
        max_length=100,
        blank=True,
        help_text=_("Email for direct contact (optional)")
    )
    

    # === STATUS & METADATA ===
    status = models.CharField(
        max_length=20,
        choices=PostStatus.choices,
        default=PostStatus.ACTIVE,
        help_text=_("Current status of the post")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def is_active(self):
        return self.status == PostStatus.ACTIVE

    def mark_as_resolved(self):
        self.status = PostStatus.RESOLVED
        self.save()

    def get_primary_image(self):
        return self.images[0] if self.images else None

    def get_available_contact_methods(self):
        methods = [ContactMethod.CHAT]
        if self.contact_phone:
            methods.append(ContactMethod.PHONE)
        if self.contact_email:
            methods.append(ContactMethod.EMAIL)

        return methods


    # === MEDIA ===
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

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class LostFoundPost(BasePost):
    pass
    images = GenericRelation(PostImage)

class AdaptionPost(BasePost):
    pass
    images = GenericRelation(PostImage)


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
