# locations/serializers.py
from rest_framework import serializers
from .models import Location


class LocationSerializer(serializers.ModelSerializer):
    # Allow writing lat/lon while keeping computed values in responses
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
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

    def validate(self, data):
        lat = data.get("latitude")
        lon = data.get("longitude")
        if (lat is None) ^ (lon is None):
            raise serializers.ValidationError("Both latitude and longitude must be provided together.")
        return data

    def get_readable(self, obj):
        parts = [obj.city, obj.country]
        if obj.district:
            parts.append(obj.district)
        readable = ", ".join([p for p in parts if p])
        if readable:
            return readable
        if obj.latitude is not None and obj.longitude is not None:
            return f"{obj.latitude}, {obj.longitude}"
        return "Unknown"
