from rest_framework import serializers
from users.models import User

class GetOrCreateChatSerializer(
    serializers.ModelSerializer):
    
    model = User
    fields = ['id']