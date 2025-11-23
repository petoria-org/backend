from typing import ClassVar

from rest_framework import viewsets

from .models import Lost_post, Found_post, Surrender_custody_pets
from .serializers import LostPostSerializer, FoundPostSerializer, SurrenderCustodyPostSerializer


class LostPostViewSet(viewsets.ModelViewSet):
    queryset: ClassVar = Lost_post.objects.all().order_by('-created_at')
    serializer_class: ClassVar = LostPostSerializer


class FoundPostViewSet(viewsets.ModelViewSet):
    queryset: ClassVar = Found_post.objects.all().order_by('-created_at')
    serializer_class: ClassVar = FoundPostSerializer


class SurrenderCustodyPostViewSet(viewsets.ModelViewSet):
    queryset: ClassVar = Surrender_custody_pets.objects.all().order_by('-created_at')
    serializer_class: ClassVar = SurrenderCustodyPostSerializer
