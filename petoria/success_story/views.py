from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from posts.pagination import PostPagination

from .models import SuccessStory, SuccessStoryImage
from .serializers import (
    SuccessStoryListSerializer,
    SuccessStorySerializer,
    SuccessStoryImageSerializer,
)


class UploadSuccessStoryImageAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded = request.FILES.getlist("file")
        if not uploaded:
            return Response({"error": "No image provided."}, status=400)

        story_images = []
        for file in uploaded:
            content_type = (file.content_type or "").lower()
            size = file.size
            allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
            max_size = 10 * 1024 * 1024  # 10 MB

            if content_type not in allowed_types:
                return Response({"error": "Unsupported file type."}, status=400)
            if size > max_size:
                return Response({"error": "File too large.", "max_bytes": max_size}, status=400)

            story_image = SuccessStoryImage.objects.create(
                uploaded_by=request.user,
                image=file,
            )
            serializer = SuccessStoryImageSerializer(story_image)
            story_images.append(serializer.data)
        
        return Response(story_images, status=201)


class DeleteSuccessStoryImageAPI(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, image_id):
        img = SuccessStoryImage.objects.filter(id=image_id, uploaded_by=request.user).first()
        if not img:
            return Response({"error": "Not found or not owned"}, status=404)

        if img.success_story and img.success_story.user != request.user:
            return Response({"error": "Not permitted to delete this image"}, status=403)

        img.image.delete(save=False)
        img.delete()
        return Response(status=204)


class ListCreateSuccessStoryAPI(ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = SuccessStoryListSerializer
    pagination_class = PostPagination

    def get_queryset(self):
        return SuccessStory.objects.all().order_by("-updated_at")

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


class ListUserSuccessStoriesAPI(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SuccessStorySerializer
    pagination_class = PostPagination

    def get_queryset(self):
        return SuccessStory.objects.filter(user=self.request.user).order_by("-updated_at")
