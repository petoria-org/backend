from django.db import models
from django.utils.translation import gettext_lazy as _


class PetType(models.TextChoices):
    DOG: str = 'dog', _('Dog')
    CAT: str = 'cat', _('Cat')
    BIRD: str = 'bird', _('Bird')
    RABBIT: str = 'rabbit', _('Rabbit')
    HAMSTER: str = 'hamster', _('Hamster')
    OTHERS: str = 'others', _('Others')

class Gender(models.TextChoices):
    MALE: str = 'male', _('Male')
    FEMALE: str = 'female', _('Female')
    UNKNOWN: str = 'unknown', _('Unknown')

class ContactMethod(models.TextChoices):
    CHAT: str = 'chat', _('In-App Chat Only')
    PHONE: str = 'phone', _('Phone Preferred')
    EMAIL: str = 'email', _('Email Preferred')
    ANY: str = 'any', _('Any Method')

class PostStatus(models.TextChoices):
    ACTIVE: str = 'active', _('Active')
    RESOLVED: str = 'resolved', _('Resolved')
    EXPIRED: str = 'expired', _('Expired')

class PostType(models.TextChoices):
    LOST: str = 'lost', _('Lost')
    FOUND: str = 'found', _('Found')
    ADOPTION: str = 'adoption', _('Adoption')

class PetSIZES(models.TextChoices):
    SMALL: str = 'small', _('Small'),
    MEDIUM: str = 'medium', _('Medium'),
    LARG: str = 'large', _('Large')

class SUITABILITY(models.TextChoices):
    Apartment: str = 'apartment', _('Suitable for Apartment')
    Garden: str = 'garden', _('Suitable for Garden')
    Family: str = 'family', _('Good for Families')
    Large_house: str = 'large_house', _('Needs Large House')
    OTHER: str = 'other', _('Other')

class HealthStatus(models.TextChoices):
    HEALTHY: str = 'healthy', _('Healthy')
    SICK: str = 'sick', _('Sick')
    INJURED: str = 'injured', _('Injured')
    UNKNOWN: str = 'unknown', _('Unknown')
