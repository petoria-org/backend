from typing import Optional, Dict, Any
from rest_framework import serializers
from .models import User
import re

class UserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields: list = [
            'id',
            'username',
            'email',
            'profile_picture',
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

    first_name = serializers.CharField(
        required=True,
        min_length=2,
        max_length=30,
    )

    last_name = serializers.CharField(
        required=True,
        min_length=2,
        max_length=30,
    )
    
    username = serializers.CharField(
        required=True,
        min_length = 2,
        max_length=50,
    )
    
    email = serializers.EmailField(
        required=True,
    )

    password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8
    )

    def validate_username(self, value):
        if not re.match(r'^[a-zA-Z0-9_.]+$', value):
            raise serializers.ValidationError(
                "Username can only contain letters, numbers, underscores and periods."
            )
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value
    
    def validate_password(self, value):
        rules = [
            (len(value) >= 8, "at least 8 characters"),
            (re.search(r'[A-Z]', value), "uppercase letters"),
            (re.search(r'[a-z]', value), "lowercase letters"),
            (re.search(r'\d', value), "numbers"),
            (re.search(r'[!@#$%^&*(),.?":{}|<>]', value), "special characters"),
        ]
        
        failed_rules = [message for condition, message in rules if not condition]
        
        if failed_rules:
            error_message = f"Password must contain {', '.join(failed_rules)}."
            raise serializers.ValidationError(error_message)
        
        return value
    
    def validate_confirm_password(self, value):
        password = self.initial_data.get('password')
        if password != value:
            error_message = 'Confirm password is not the same as password.'
            raise serializers.ValidationError(error_message)
        return value
    

    def create(self, validated_data: Dict[str, Any]) -> User:
        user = User.objects.create_user(
            first_name = validated_data.get('first_name'),
            last_name = validated_data.get('last_name'),
            username=validated_data.get('username'),
            email=validated_data.get('email'),
            password=validated_data.get('password')
        )
        user.is_active = False
        user.save()
        return user

class VerifyOTPSerializer(serializers.Serializer):
    purpose = serializers.ChoiceField(
        choices=["email", "reset"],
        required=True
    )
    email = serializers.EmailField(required=True)
    code = serializers.CharField(min_length=6, max_length=6, required=True)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        user = User.objects.filter(email=attrs['email']).first()
        if not user:
            raise serializers.ValidationError({"email": "User not found."})
        return attrs



class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(required=False, write_only=True)

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
