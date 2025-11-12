from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from users.models import User
from .enums import PetType, AgeEstimate, Gender, ContactMethod, PostStatus
from django.core.validators import RegexValidator


'''
things to consider: 

1) how locations should be handled (necessary or not)
2) if email/phone contact is set then should it be verified and how
3) how should images be validated to have the appropriate size and format
4) setting auto-expiration for posts
5) create child post models

'''


class BasePost(models.Model):
    # === CORE POST INFORMATION ===
    title = models.CharField(
        max_length=200,
        help_text=_("Clear, descriptive title for the post")
    )
    description = models.TextField(
        max_length=5000,
        blank=True,
        help_text=_("Detailed description of the pet and situation")
    )
    
    # === PET IDENTIFICATION ===
    pet_type = models.CharField(
        max_length=20,
        choices=PetType.choices,
        help_text=_("Type of pet")
    )

    breed = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Breed of the pet (leave blank if unknown)")
    )

    color = models.CharField(
        max_length=100,
        help_text=_("Color and distinctive markings")
    )

    # EXACT AGE - for owners who know precise age
    age = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("Exact age (e.g., '2 years 3 months', '8 months', '5 years')")
    )

    gender = models.CharField(
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
    
    # === Location for Map Integration ===
    location = models.CharField(
        max_length=255,
        blank=True,
        help_text="Neighborhood or area name"
    )
    
    location_point = models.PointField(
        null=True,
        blank=True,
        help_text="Exact map coordinates"
    )
    
    location_radius = models.PositiveIntegerField(
        default=10,
        help_text="Search radius in kilometers for pet matches"
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
    contact_email = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Email for direct contact (optional)")
    )
    preferred_contact = models.CharField(
        max_length=10,
        choices=ContactMethod.choices,
        default=ContactMethod.CHAT,
        help_text=_("Preferred method of contact")
    )
    
    # === MEDIA ===
    images = models.JSONField(
        default=list,
        blank=True,
        help_text=_("List of image URLs for the post")
    )
    
    # === STATUS & METADATA ===
    status = models.CharField(
        max_length=20,
        choices=PostStatus.choices,
        default=PostStatus.ACTIVE,
        help_text=_("Current status of the post")
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)ss'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        help_text=_("When this post automatically expires")
    )
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_pet_type_display()}"
    
    def clean(self):
        """Validation for all posts"""
        errors = {}
        
        if not self.title or len(self.title.strip()) < 5:
            errors['title'] = _('Title must be at least 5 characters long')
        
        if not self.description or len(self.description.strip()) < 10:
            errors['description'] = _('Description must be at least 10 characters long')
        
        if not self.address:
            errors['address'] = _('Address is required')
        
        # Contact validation
        if self.preferred_contact == ContactMethod.PHONE and not self.contact_phone:
            errors['contact_phone'] = _('Phone number is required when phone is preferred contact')
        elif self.preferred_contact == ContactMethod.EMAIL and not self.contact_email:
            errors['contact_email'] = _('Email is required when email is preferred contact')
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def is_active(self):
        return self.status == PostStatus.ACTIVE
    
    def mark_as_resolved(self):
        self.status = PostStatus.RESOLVED
        self.save()
    
    def has_expired(self):
        return timezone.now() > self.expires_at
    
    def get_primary_image(self):
        return self.images[0] if self.images else None
    
    def get_available_contact_methods(self):
        methods = [ContactMethod.CHAT]
        
        if self.contact_phone:
            methods.append(ContactMethod.PHONE)
        if self.contact_email:
            methods.append(ContactMethod.EMAIL)
            
        return methods


# class Post(models.Model):
#     author = models.ForeignKey(
#         'users.User',
#         on_delete=models.CASCADE
#         )
    
#     title = models.CharField(max_length=80)
    
#     description = RichTextField()
    
#     award = models.IntegerField(
#         max_digits=12, 
#         validators=[
#             MinValueValidator(10000, message="Award must be at least 10000")
#         ]
#     )
    
#     date_created = models.DateTimeField(auto_now_add=True)
    
#     phone = models.CharField(
#         max_length=11,
#         blank=True,
#         null=True,
#         validators=[
#             RegexValidator(
#                 regex=r'^09[0-9]{9}$',
#                 message="Phone must start with 09 and contain 11 digits total."
#             )
#         ]
#     )
    
#     CONDITION = ()
#     state = models.ForeignKey('State', on_delete=models.PROTECT, null=False, related_name='posts')
#     category = models.ForeignKey('Category', on_delete=models.PROTECT, null=True, related_name='posts')
#     condition = models.CharField(max_length=100, choices=CONDITION)
#     ## is_featured = models.BooleanField(default=False)


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