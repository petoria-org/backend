from django.db import models
from django.utils.translation import gettext_lazy as _

class HealthStatus(models.TextChoices):
    HEALTHY = 'healthy', _('Healthy')
    SICK = 'sick', _('Sick')
    INJURED = 'injured', _('Injured')
    UNKNOWN = 'unknown', _('Unknown')

class PetType(models.TextChoices):
    DOG = 'dog', _('Dog')
    CAT = 'cat', _('Cat')
    BIRD = 'bird', _('Bird')
    RABBIT = 'rabbit', _('Rabbit')
    FISH = 'fish', _('Fish')
    REPTILE = 'reptile', _('Reptile')
    SMALL_ANIMAL = 'small_animal', _('Small Animal')
    OTHER = 'other', _('Other')


class Gender(models.TextChoices):
    MALE = 'male', _('Male')
    FEMALE = 'female', _('Female')
    UNKNOWN = 'unknown', _('Unknown')

class ContactMethod(models.TextChoices):
    CHAT = 'chat', _('In-App Chat Only')
    PHONE = 'phone', _('Phone Preferred')
    EMAIL = 'email', _('Email Preferred')
    ANY = 'any', _('Any Method')

class PostStatus(models.TextChoices):
    ACTIVE = 'active', _('Active')
    RESOLVED = 'resolved', _('Resolved')
    EXPIRED = 'expired', _('Expired')

class PostType(models.TextChoices):
    LOST = 'lost', _('Lost')
    FOUND = 'found', _('Found')
    ADOPTION = 'adoption', _('Adoption')

class Pet_SIZES(models.TextChoices):
    SMALL = 'small', _('Small'),
    MEDIUM = 'medium', _('Medium'),
    LARG = 'large', _('Large')

class SUITABILITY(models.TextChoices):
    Apartment = 'apartment', _('Suitable for Apartment')
    Garden = 'garden', _('Suitable for Garden')
    Family = 'family', _('Good for Families')
    Large_house = 'large_house', _('Needs Large House')
    OTHER = 'other', _('Other')



