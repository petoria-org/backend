import phonenumbers
from rest_framework import serializers

class RegisterSerializer(serializers.Serializer):
    phone = serializers.CharField()

    def validate_phone(self, value):
        try:
            number = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(number):
                raise serializers.ValidationError("Invalid phone number.")
        except:
            raise serializers.ValidationError("Invalid phone format.")

        return value
