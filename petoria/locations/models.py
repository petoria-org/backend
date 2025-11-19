from django.contrib.gis.db import models

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
