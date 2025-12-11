from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListAPIView
from posts.pagination import PostPagination  # اگر ندارید، می‌تونید از PageNumberPagination خود DRF استفاده کنید
from posts.pagination import PostPagination  # یا از DRF default Pagination استفاده کن
from rest_framework.generics import ListCreateAPIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated

from .models import SuccessStory
from .serializers import SuccessStoryListSerializer
from .serializers import SuccessStorySerializer


class ListCreateSuccessStoryAPI(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SuccessStorySerializer
    pagination_class = PostPagination

    def get_queryset(self):
        return SuccessStory.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ListCreateSuccessStoryAPI(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SuccessStorySerializer
    pagination_class = PostPagination

    def get_queryset(self):
        return SuccessStory.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RetrieveUpdateDeleteSuccessStoryAPI(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = SuccessStory.objects.all()
    serializer_class = SuccessStorySerializer

    def get_object(self):
        obj = super().get_object()
        if obj.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to modify this story.")
        return obj


class ListAllSuccessStoriesAPI(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = SuccessStoryListSerializer
    pagination_class = PostPagination
    queryset = SuccessStory.objects.all().order_by("-created_at")
