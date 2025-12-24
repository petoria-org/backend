from rest_framework import serializers

from .models import SuccessStory, SuccessStoryImage


class SuccessStoryImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = SuccessStoryImage
        fields = ["id", "image"]


class SuccessStorySerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(source="user.if", read_only=True)
    user_name = serializers.CharField(source="user.username", read_only=True)
    images = SuccessStoryImageSerializer(many=True, read_only=True)
    image_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True,
        help_text="IDs returned from /SuccessStory/images/upload/"
    )

    class Meta:
        model = SuccessStory
        fields = [
            "id",
            "user_id",
            "user_name",
            "story_type",
            "title",
            "story",
            "image_ids",
            "images",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user_name", "created_at", "updated_at", "images"]

    def _bind_images(self, instance, image_ids, user):
        if not image_ids:
            return

        unique_ids = list(set(image_ids))
        images = SuccessStoryImage.objects.filter(
            id__in=unique_ids,
            uploaded_by=user,
        )

        found_ids = {img.id for img in images}
        missing_ids = [img_id for img_id in unique_ids if img_id not in found_ids]

        bound_to_other = []
        new_image_ids = []
        for img in images:
            if img.success_story_id is None:
                new_image_ids.append(img.id)
            elif img.success_story_id == instance.id:
                continue
            else:
                bound_to_other.append(img.id)

        if missing_ids or bound_to_other:
            raise serializers.ValidationError(
                {
                    "image_ids": "One or more image IDs are invalid or already bound to another story.",
                    "missing_ids": missing_ids,
                    "bound_elsewhere": bound_to_other,
                }
            )

        existing_count = instance.images.count()
        if existing_count + len(new_image_ids) > 7:
            raise serializers.ValidationError({"images": "Each story cannot have more than 7 photos."})

        if new_image_ids:
            SuccessStoryImage.objects.filter(id__in=new_image_ids).update(success_story=instance)

    def create(self, validated_data):
        image_ids = validated_data.pop("image_ids", [])
        request = self.context.get("request") if hasattr(self, "context") else None
        if request and hasattr(request, "user") and request.user.is_authenticated:
            validated_data.setdefault("user", request.user)

        story = SuccessStory.objects.create(**validated_data)
        user = validated_data.get("user") or (request.user if request else None)
        if user:
            self._bind_images(story, image_ids, user)
        return story

    def update(self, instance, validated_data):
        image_ids = validated_data.pop("image_ids", [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        request = self.context.get("request") if hasattr(self, "context") else None
        user = validated_data.get("user") or (request.user if request else None)
        if user and image_ids:
            self._bind_images(instance, image_ids, user)
        return instance


class SuccessStoryListSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)
    image = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SuccessStory
        fields = ["id", "user_name", "title", "story_type", "image", "created_at"]

    def get_image(self, obj):
        first = obj.images.first()
        return first.image.url if first else None
