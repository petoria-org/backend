from django.contrib.gis.geos import Point
from locations.models import Location
from locations.serializers import LocationSerializer
from rest_framework import serializers

from .models import LostPost, FoundPost, SurrenderCustodyPet, PostImage


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ["id", "image", "thumbnail"]


class BasePostSerializer(serializers.ModelSerializer):
    images = PostImageSerializer(many=True, read_only=True)
    location = LocationSerializer(required=False)

    class Meta:
        model = None  # To be set in child serializers
        fields = [
            "id", "title", "description",
            "pet_type", "pet_sex", "pet_name", "pet_age", "breed", "Specific_symptoms",
            "location",
            "contact_phone", "contact_email",
            "status",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "images"]

    def validate(self, data):
        location_data = data.get("location")
        model_name = self.Meta.model.__name__

        # Lost_post must have a location
        if model_name == "LostPost" and not location_data:
            raise serializers.ValidationError(
                "Location is required for lost-pet posts."
            )
        # If location is provided, at least city or country should exist
        if location_data:
            if not (location_data.get("city") or location_data.get("country")):
                raise serializers.ValidationError(
                    "City or country must be provided when location is given."
                )
        return data

    def _handle_location(self, instance, location_data):
        """
        Create or update the related Location from nested data.
        """
        if location_data is None:
            return instance.location if instance else None

        lat = location_data.pop("latitude", None)
        lon = location_data.pop("longitude", None)
        if lat is not None and lon is not None:
            location_data["point"] = Point(lon, lat)

        if instance and instance.location:
            # Update existing location
            for attr, value in location_data.items():
                setattr(instance.location, attr, value)
            instance.location.save()
            return instance.location

        # Create a new location
        return Location.objects.create(**location_data)

    def create(self, validated_data):
        location_data = validated_data.pop("location", None)

        # Attach request user if available; otherwise expect client to provide
        request = self.context.get("request") if hasattr(self, "context") else None
        if request and hasattr(request, "user") and request.user.is_authenticated:
            validated_data.setdefault("user", request.user)

        location = self._handle_location(instance=None, location_data=location_data)
        return self.Meta.model.objects.create(location=location, **validated_data)

    def update(self, instance, validated_data):
        location_data = validated_data.pop("location", None)
        if location_data is not None:
            instance.location = self._handle_location(instance, location_data)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ------------------------------
# Child Serializers
# ------------------------------
class LostPostSerializer(BasePostSerializer):
    class Meta(BasePostSerializer.Meta):
        model = LostPost
        fields = BasePostSerializer.Meta.fields + ["lost_time"]


class FoundPostSerializer(BasePostSerializer):
    class Meta(BasePostSerializer.Meta):
        model = FoundPost
        fields = BasePostSerializer.Meta.fields + ["found_time"]


class SurrenderCustodyPostSerializer(BasePostSerializer):
    class Meta(BasePostSerializer.Meta):
        model = SurrenderCustodyPet
        fields = BasePostSerializer.Meta.fields + [
            "diseases",
            "has_birth_certificate",
            "vaccination",
            "steriliz",
        ]


# ------------------------------
# List Serializers (For Showing in List Page)
# ------------------------------
class LostPostListSerializer(serializers.ModelSerializer):
    thumbnail: str = serializers.SerializerMethodField()

    class Meta:
        model = LostPost
        fields = ["id", "title", "pet_type", "lost_time", "thumbnail", "created_at"]

    def get_thumbnail(self, obj):
        if obj.images.exists():
            return obj.images.first().thumbnail.url
        return None


class FoundPostListSerializer(serializers.ModelSerializer):
    thumbnail: str = serializers.SerializerMethodField()

    class Meta:
        model = FoundPost
        fields = ["id", "title", "pet_type", "found_time", "thumbnail", "created_at"]

    def get_thumbnail(self, obj):
        if obj.images.exists():
            return obj.images.first().thumbnail.url
        return None


class SurrenderPostListSerializer(serializers.ModelSerializer):
    thumbnail: str = serializers.SerializerMethodField()

    class Meta:
        model = SurrenderCustodyPet
        fields = ["id", "title", "pet_type", "thumbnail", "created_at"]

    def get_thumbnail(self, obj):
        if obj.images.exists():
            return obj.images.first().thumbnail.url
        return None
