from locations.models import Location
from locations.serializers import LocationSerializer
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from .models import LostPost, FoundPost, SurrenderCustodyPet, PostImage, PetAge


class PostImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = PostImage
        fields = ["id", "image"]


class PetAgeSerializer(serializers.ModelSerializer):
    display = serializers.CharField(read_only=True)

    class Meta:
        model = PetAge
        fields = ["years", "months", "display"]

    def validate(self, data):
        if data.get("years") is None and data.get("months") is None:
            raise serializers.ValidationError("Provide years or months for pet age.")
        return data


class BasePostSerializer(serializers.ModelSerializer):
    images = PostImageSerializer(many=True, read_only=True)
    location = LocationSerializer(required=False)
    pet_age = PetAgeSerializer(required=False, allow_null=True)
    image_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True,
        help_text="IDs returned from /posts/images/upload/"
    )
    user_id = serializers.SerializerMethodField(read_only=True)
    email = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = None
        fields = [
            "id", "title", "description",
            "pet_type", "pet_sex", "pet_name", "pet_age", "breed", "Specific_symptoms",
            "location",
            "user_id", "email",
            "status",
            "images",
            "image_ids",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "images"]

    def get_user_id(self, obj):
        return obj.user.id
    
    def get_email(self, obj):
        if obj.contact_email :
            return obj.user.email
        return None

    def validate(self, data):
        location_data = data.get("location")
        model_name = self.Meta.model.__name__
        
        # Get the instance if this is an update
        instance = getattr(self, 'instance', None)
        
        # Lost_post must have a location on CREATE only
        if model_name == "LostPost" and not location_data and not instance:
            raise serializers.ValidationError(
                "Location is required for lost-pet posts."
            )
        
        # If this is an update for LostPost, prevent location deletion
        if model_name == "LostPost" and instance and location_data is None:
            # location_data is None when key is missing from request
            # This is fine - don't update location
            pass
        elif model_name == "LostPost" and instance and location_data is not None:
            # location_data exists in request
            if location_data == {}:
                # Empty dict - probably trying to clear location
                raise serializers.ValidationError(
                    {"location": "Location cannot be removed from lost-pet posts."}
                )
        
        # If location is provided (not None or empty dict), validate its content
        if location_data:
            lat = location_data.get("latitude")
            lon = location_data.get("longitude")
            has_coords = lat is not None and lon is not None
            has_city_or_country = bool(location_data.get("city") or location_data.get("country"))
            if (lat is None) ^ (lon is None):
                raise serializers.ValidationError(
                    {"location": "Both latitude and longitude must be provided together."}
                )
            if not (has_coords or has_city_or_country):
                raise serializers.ValidationError(
                    {"location": "Provide city/country or latitude/longitude when location is given."}
                )
        return data

    def _bind_images(self, instance, image_ids, user):
        if not image_ids:
            return

        # Ensure IDs are unique
        unique_ids = list(set(image_ids))

        # Fetch all images for this user, whether bound or not
        images = PostImage.objects.filter(
            id__in=unique_ids,
            uploaded_by=user
        )

        found_ids = {img.id for img in images}
        missing_ids = [img_id for img_id in unique_ids if img_id not in found_ids]

        # Allow already-bound images if they belong to this instance (so re-sending does not error)
        ct = ContentType.objects.get_for_model(instance.__class__)
        bound_to_other = []
        new_image_ids = []
        for img in images:
            if img.content_type_id is None and img.object_id is None:
                new_image_ids.append(img.id)
            elif img.content_type_id == ct.id and img.object_id == instance.id:
                # Already bound to this post; allow and skip rebinding
                continue
            else:
                bound_to_other.append(img.id)

        if missing_ids or bound_to_other:
            raise serializers.ValidationError(
                {
                    "image_ids": "One or more image IDs are invalid or already bound to another post.",
                    "missing_ids": missing_ids,
                    "bound_elsewhere": bound_to_other,
                }
            )

        existing_count = instance.images.count()
        if existing_count + len(new_image_ids) > 7:
            raise serializers.ValidationError({"images": "Each post cannot have more than 7 photos."})

        if new_image_ids:
            PostImage.objects.filter(id__in=new_image_ids).update(content_type=ct, object_id=instance.id)

    def _handle_location(self, instance, location_data):
        """
        Create or update the related Location from nested data.
        """
        if location_data is None:
            return instance.location if instance else None

        if instance and instance.location:
            # Update existing location
            for attr, value in location_data.items():
                setattr(instance.location, attr, value)
            instance.location.save()
            return instance.location

        # Create a new location
        return Location.objects.create(**location_data)

    def _handle_pet_age(self, instance, pet_age_data):
        if pet_age_data is serializers.empty:
            return instance.pet_age if instance else None
        if pet_age_data is None:
            if instance and instance.pet_age:
                instance.pet_age.delete()
            return None
        if instance and instance.pet_age:
            for attr, value in pet_age_data.items():
                setattr(instance.pet_age, attr, value)
            instance.pet_age.save()
            return instance.pet_age
        return PetAge.objects.create(**pet_age_data)

    def create(self, validated_data):
        location_data = validated_data.pop("location", None)
        pet_age_data = validated_data.pop("pet_age", serializers.empty)
        image_ids = validated_data.pop("image_ids", [])

        # Attach request user if available; otherwise expect client to provide
        request = self.context.get("request") if hasattr(self, "context") else None
        if request and hasattr(request, "user") and request.user.is_authenticated:
            validated_data.setdefault("user", request.user)

        location = self._handle_location(instance=None, location_data=location_data)
        pet_age = self._handle_pet_age(instance=None, pet_age_data=pet_age_data)
        post = self.Meta.model.objects.create(
            location=location,
            pet_age=pet_age,
            **validated_data
        )
        user = validated_data.get("user") or (request.user if request else None)
        if user:
            self._bind_images(post, image_ids, user)
        return post

    def update(self, instance, validated_data):
        location_data = validated_data.pop("location", None)
        pet_age_data = validated_data.pop("pet_age", serializers.empty)
        image_ids = validated_data.pop("image_ids", [])
        if location_data is not None:
            instance.location = self._handle_location(instance, location_data)
        if pet_age_data is not serializers.empty:
            instance.pet_age = self._handle_pet_age(instance, pet_age_data)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        request = self.context.get("request") if hasattr(self, "context") else None
        user = validated_data.get("user") or (request.user if request else None)
        if user and image_ids:
            self._bind_images(instance, image_ids, user)

        return instance


# ------------------------------
# Child Serializers
# ------------------------------
class LostPostSerializer(BasePostSerializer):
    post_type = serializers.SerializerMethodField(read_only=True)

    class Meta(BasePostSerializer.Meta):
        model = LostPost
        fields = BasePostSerializer.Meta.fields + ["lost_time", "post_type"]
    
    def get_post_type(self, obj):
        return "lost"


class FoundPostSerializer(BasePostSerializer):
    post_type = serializers.SerializerMethodField(read_only=True)

    class Meta(BasePostSerializer.Meta):
        model = FoundPost
        fields = BasePostSerializer.Meta.fields + ["found_time", "post_type"]

    def get_post_type(self, obj):
        return "found"


class SurrenderCustodyPostSerializer(BasePostSerializer):
    post_type = serializers.SerializerMethodField(read_only=True)
    
    class Meta(BasePostSerializer.Meta):
        model = SurrenderCustodyPet
        fields = BasePostSerializer.Meta.fields + [
            "diseases",
            "has_birth_certificate",
            "vaccination",
            "steriliz",
            "post_type"
        ]
    
    def get_post_type(self, obj):
        return "adoption"


# ------------------------------
# List Serializers (For Showing in List Page)
# ------------------------------
class LostPostListSerializer(serializers.ModelSerializer):
    thumbnail: str = serializers.SerializerMethodField()
    location = LocationSerializer(read_only=True)
    post_type = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = LostPost
        fields =[
            "id",
            "post_type",
            "title",
            "breed",
            "description",
            "pet_type",
            "location",
            "lost_time",
            "thumbnail",
            "updated_at"
        ]

    def get_thumbnail(self, obj):
        if obj.images.exists():
            return obj.images.first().image.url
        return None
    
    def get_post_type(self, obj):
        return "lost"


class FoundPostListSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField(read_only=True)
    location = LocationSerializer(read_only=True)
    post_type = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FoundPost
        fields =[
            "id",
            "post_type",
            "title",
            "breed",
            "description",
            "pet_type",
            "location",
            "found_time",
            "thumbnail",
            "updated_at"
        ]

    def get_thumbnail(self, obj):
        if obj.images.exists():
            return obj.images.first().image.url
        return None
    
    def get_post_type(self, obj):
        return "found"


class SurrenderPostListSerializer(serializers.ModelSerializer):
    thumbnail: str = serializers.SerializerMethodField()
    location = LocationSerializer(read_only=True)
    post_type = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SurrenderCustodyPet
        fields =[
            "id",
            "post_type",
            "title",
            "breed",
            "description",
            "pet_type",
            "location",
            "thumbnail",
            "updated_at"
        ]

    def get_thumbnail(self, obj):
        if obj.images.exists():
            return obj.images.first().image.url
        return None
    
    def get_post_type(self, obj):
        return "adoption"
