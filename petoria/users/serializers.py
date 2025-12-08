from typing import Optional, Dict, Any

from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    profile_picture: serializers.SerializerMethodField = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields: list = [
            'id',
            'username',
            'email',
            'phone_number',
            'profile_picture',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_profile_picture(self, obj: User) -> Optional[str]:
        try:
            if obj.profile_picture:
                return obj.profile_picture.url
            else:
                return None
        except Exception:
            return None


class SignupSerializer(serializers.Serializer):
    username: serializers.CharField = serializers.CharField(max_length=150)
    email: serializers.EmailField = serializers.EmailField()
    password: serializers.CharField = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs: dict[str, Any]) -> Dict[str, Any]:
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("Email already exists.")
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError("Username already exists.")
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> User:
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        user.is_active = False
        user.save()
        return user


class VerifyOTPSerializer(serializers.Serializer):
    email: serializers.EmailField = serializers.EmailField()
    code: serializers.CharField = serializers.CharField(max_length=6)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        user = User.objects.filter(email=attrs['email']).first()
        if not user:
            raise serializers.ValidationError("User not found.")
        return attrs


class LoginSerializer(serializers.Serializer):
    identifier: serializers.CharField = serializers.CharField()
    password: serializers.CharField = serializers.CharField(required=False, write_only=True)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        identifier: str = attrs.get('identifier')

        # login with email or username
        user: Optional[User] = (
                User.objects.filter(email=identifier).first() or
                User.objects.filter(username=identifier).first()
        )

        if not user:
            raise serializers.ValidationError("User not found.")

        attrs['user'] = user
        return attrs
