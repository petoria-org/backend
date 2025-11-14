from .models import User
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer


class BasicUserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

    
class BasicWithPFPUserSerializer(ModelSerializer):
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'profile_picture']

    def get_profile_picture(self, obj):
        if obj.profile_picture and hasattr(obj.profile_picture, 'url'):
            return obj.profile_picture.url
        return None
