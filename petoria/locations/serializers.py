from rest_framework import serializers
from django.contrib.gis.geos import Point
from .models import Location

class LocationSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)

    class Meta:
        model = Location
        fields = ["id", "country", "city", "district", "full_address", "latitude", "longitude"]
        read_only_fields = ["country", "city", "district", "full_address"]

    def create(self, validated_data):
        lat = validated_data.pop('latitude')
        lon = validated_data.pop('longitude')
        validated_data['point'] = Point(lon, lat) # دقت کنید: ابتدا طول جغرافیایی
        return super().create(validated_data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.point:
            ret['latitude'] = instance.point.y
            ret['longitude'] = instance.point.x
        return ret