from rest_framework import serializers

from .models import SuccessStory


class SuccessStorySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = SuccessStory
        fields = ['id', 'user_name', 'title', 'story', 'story_type', 'created_at']
        read_only_fields = ['id', 'user_name', 'created_at']


# stories/serializers.py
from rest_framework import serializers
from .models import SuccessStory


class SuccessStorySerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = SuccessStory
        fields = ['id', 'user', 'post_type', 'title', 'content', 'created_at']


class SuccessStoryListSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = SuccessStory
        fields = ['id', 'user', 'post_type', 'title', 'created_at']
