from django.db import models


class AttachmentType(models.TextChoices):
    IMAGE = "image", "Image"
    VIDEO = "video", "Video"
    OTHER = "other", "Other"
