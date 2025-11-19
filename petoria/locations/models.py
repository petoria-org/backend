from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _

class Location(models.Model):

    country = models.CharField(
        max_length = 150,
        blank = True,
        null = True
    )

    city = models.CharField(
        max_length = 120,
        blank = True,
        null = True
    )

    district = models.CharField(
        max_length = 120,
        blank = True,
        null = True
    )

    # ==== (latitude/longitude) ===
    point = models.PointField(
        geography = True,
        null = True,
        blank = True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        if self.point:
            return f"({self.point.y:.4f}, {self.point.x:.4f})"
        parts = [self.country, self.city, self.district]
        readable = ", ".join([p for p in parts if p])
        return readable or "Unknown Location"

        if self.point:
            return f"({self.point.y:.4f}, {self.point.x:.4f})"

        return "Unknown Location"















class Location(models.Model):
    # The geographic point (latitude/longitude)
    point = models.PointField(geography=True)

    # Optional descriptive fields
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.address:
            return self.address
        return f"({self.point.y:.4f}, {self.point.x:.4f})"
