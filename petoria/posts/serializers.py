from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from phonenumber_field.phonenumber import PhoneNumber
from locations.serializers import LocationSerializer
from .models import Lost_post, Found_post, Surrender_custody_pets, PostImage


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
        if model_name == "Lost_post" and not location_data:
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


# ------------------------------
# Child Serializers
# ------------------------------
class LostPostSerializer(BasePostSerializer):
    class Meta(BasePostSerializer.Meta):
        model = Lost_post
        fields = BasePostSerializer.Meta.fields + ["lost_time"]


class FoundPostSerializer(BasePostSerializer):
    class Meta(BasePostSerializer.Meta):
        model = Found_post
        fields = BasePostSerializer.Meta.fields + ["found_time"]


class SurrenderCustodyPostSerializer(BasePostSerializer):
    class Meta(BasePostSerializer.Meta):
        model = Surrender_custody_pets
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
        model = Lost_post
        fields = ["id", "title", "pet_type", "lost_time", "thumbnail"]

    def get_thumbnail(self, obj):
        if obj.images.exists():
            return obj.images.first().thumbnail.url
        return None


class FoundPostListSerializer(serializers.ModelSerializer):
    thumbnail: str = serializers.SerializerMethodField()

    class Meta:
        model = Found_post
        fields = ["id", "title", "pet_type", "found_time", "thumbnail"]

    def get_thumbnail(self, obj):
        if obj.images.exists():
            return obj.images.first().thumbnail.url
        return None


class SurrenderPostListSerializer(serializers.ModelSerializer):
    thumbnail: str = serializers.SerializerMethodField()

    class Meta:
        model = Surrender_custody_pets
        fields = ["id", "title", "pet_type", "thumbnail"]

    def get_thumbnail(self, obj):
        if obj.images.exists():
            return obj.images.first().thumbnail.url
        return None