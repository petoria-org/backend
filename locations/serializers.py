# locations/serializers.py
from rest_framework import serializers
from .models import Location


class LocationSerializer(serializers.ModelSerializer):
    # Allow writing lat/lon while keeping computed values in responses
    latitude = serializers.FloatField(required=False, write_only=True)
    longitude = serializers.FloatField(required=False, write_only=True)
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

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Expose lat/lon from point in responses
        data["latitude"] = instance.point.y if instance.point else None
        data["longitude"] = instance.point.x if instance.point else None
        return data

    def get_readable(self, obj):
        if obj.point:
            return f"{obj.city}, {obj.country}"
        parts = [obj.country, obj.city]
        if obj.district:
            parts.append(obj.district)
        return ", ".join(parts) or "Unknown"
