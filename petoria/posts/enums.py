from django.db import models
from django.utils.translation import gettext_lazy as _


class PetType(models.TextChoices):
    DOG = 'dog', _('Dog')
    CAT = 'cat', _('Cat')
    BIRD = 'bird', _('Bird')
    RABBIT = 'rabbit', _('Rabbit')
    FISH = 'fish', _('Fish')
    REPTILE = 'reptile', _('Reptile')
    SMALL_ANIMAL = 'small_animal', _('Small Animal')
    OTHER = 'other', _('Other')

class AgeEstimate(models.TextChoices):
    BABY = 'baby', _('Baby (0-1 year)')
    YOUNG = 'young', _('Young (1-3 years)')
    ADULT = 'adult', _('Adult (3-8 years)')
    SENIOR = 'senior', _('Senior (8+ years)')
    UNKNOWN = 'unknown', _('Unknown')

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
