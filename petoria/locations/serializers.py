# locations/serializers.py
from rest_framework import serializers
from .models import Location


class LocationSerializer(serializers.ModelSerializer):
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    readable = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = [
            "id",
            "country",
            "city",
            "district",
            "latitude",
            "longitude",
            "readable",
        ]

    def get_latitude(self, obj):
        return obj.point.y if obj.point else None

    def get_longitude(self, obj):
        return obj.point.x if obj.point else None

    def get_readable(self, obj):
        if obj.point:
            return f"{obj.city}, {obj.country}"
        parts = [obj.country, obj.city]
        if obj.district:
            parts.append(obj.district)
        return ", ".join(parts) or "Unknown"