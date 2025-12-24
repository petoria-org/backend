from typing import Any, List, Dict
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from .models import LostPost, FoundPost, SurrenderCustodyPet, PostImage
from .pagination import PostPagination
from .serializers import (
    LostPostSerializer, FoundPostSerializer, SurrenderCustodyPostSerializer,
    LostPostListSerializer, FoundPostListSerializer, SurrenderPostListSerializer,
    PostImageSerializer
)


# ================================
#   POST IMAGES UPLOAD
# ================================
class UploadPostImageAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded = request.FILES.get("image") or request.FILES.get("file")
        if not uploaded:
            return Response({"error": "No image provided. Use form-data key 'image' or 'file'."}, status=400)

        content_type = (uploaded.content_type or "").lower()
        size = uploaded.size
        allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
        max_size = 10 * 1024 * 1024  # 10 MB

        if content_type not in allowed_types:
            return Response({"error": "Unsupported file type."}, status=400)
        if size > max_size:
            return Response({"error": "File too large.", "max_bytes": max_size}, status=400)

        post_image = PostImage.objects.create(
            uploaded_by=request.user,
            image=uploaded,
        )
        serializer = PostImageSerializer(post_image)
        return Response(serializer.data, status=201)


class DeletePostImageAPI(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, image_id):
        img = PostImage.objects.filter(id=image_id, uploaded_by=request.user).first()
        if not img:
            return Response({"error": "Not found or not owned"}, status=404)

        # If already bound to a post, ensure the requester owns that post
        if img.post and img.post.user != request.user:
            return Response({"error": "Not permitted to delete this image"}, status=403)

        img.image.delete(save=False)
        img.delete()
        return Response(status=204)


# ================================
#   USER ALL POSTS (lost + found + custody)
# ================================
class ListAllPostsUserAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        lost = LostPost.objects.filter(user=user)
        found = FoundPost.objects.filter(user=user)
        surrender = SurrenderCustodyPet.objects.filter(user=user)

        combined: List[Dict[str, Any]] = []

        for obj in lost:
            data = LostPostListSerializer(obj).data
            data["type"] = "lost"
            combined.append(data)

        for obj in found:
            data = FoundPostListSerializer(obj).data
            data["type"] = "found"
            combined.append(data)

        for obj in surrender:
            data = SurrenderPostListSerializer(obj).data
            data["type"] = "surrender"
            combined.append(data)

        combined.sort(key=lambda x: x["updated_at"], reverse=True)

        paginator = PostPagination()
        page = paginator.paginate_queryset(combined, request)
        return paginator.get_paginated_response(page)


# ================================
#   USER POSTS (SEPARATE)
# ================================
class ListUserLostPostsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        posts = LostPost.objects.filter(user=request.user).order_by("-updated_at")
        paginator = PostPagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = LostPostListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ListUserFoundPostsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        posts = FoundPost.objects.filter(user=request.user).order_by("-updated_at")
        paginator = PostPagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = FoundPostListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ListUserCustodyPostsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        posts = SurrenderCustodyPet.objects.filter(user=request.user).order_by("-updated_at")
        paginator = PostPagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = SurrenderPostListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# ================================
#   ALL POSTS (lost + found + custody) PUBLIC
# ================================
class ListAllPostsAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        lost = LostPost.objects.all().order_by("-updated_at")
        found = FoundPost.objects.all().order_by("-updated_at")
        surrender = SurrenderCustodyPet.objects.all().order_by("-updated_at")

        combined = []

        for obj in lost:
            data = LostPostListSerializer(obj).data
            data["type"] = "lost"
            combined.append(data)

        for obj in found:
            data = FoundPostListSerializer(obj).data
            data["type"] = "found"
            combined.append(data)

        for obj in surrender:
            data = SurrenderPostListSerializer(obj).data
            data["type"] = "surrender"
            combined.append(data)

        combined.sort(key=lambda x: x["updated_at"], reverse=True)

        paginator = PostPagination()
        page = paginator.paginate_queryset(combined, request)
        return paginator.get_paginated_response(page)


# ================================
#   LOST POSTS CRUD
# ================================
class ListCreateLostPostAPI(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        posts = LostPost.objects.all().order_by('-created_at')
        paginator = PostPagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = LostPostListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = LostPostSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class RetrieveUpdateDeleteLostPostAPI(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        return LostPost.objects.filter(pk=pk).first()

    def get(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return Response({"error": "Not Found"}, 404)
        return Response(LostPostSerializer(post).data)

    def put(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return Response({"error": "Not Found"}, 404)

        updated_data = request.data.copy()
        updated_data["updated_at"] = timezone.now().isoformat()
        serializer = LostPostSerializer(post, data=updated_data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, 400)

    def delete(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return Response({"error": "Not Found"}, 404)
        post.delete()
        return Response(status=204)


# ================================
#   FOUND POSTS CRUD
# ================================
class ListCreateFoundPostAPI(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        posts = FoundPost.objects.all().order_by('-updated_at')
        paginator = PostPagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = FoundPostListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = FoundPostSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, 201)
        return Response(serializer.errors, 400)


class RetrieveUpdateDeleteFoundPostAPI(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        return FoundPost.objects.filter(pk=pk).first()

    def get(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return Response({"error": "Not Found"}, 404)
        return Response(FoundPostSerializer(post).data)

    def put(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return Response({"error": "Not Found"}, 404)

        updated_data = request.data.copy()
        updated_data["updated_at"] = timezone.now().isoformat()
        serializer = FoundPostSerializer(post, data=updated_data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, 400)

    def delete(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return Response({"error": "Not Found"}, 404)
        post.delete()
        return Response(status=204)


# ================================
#   CUSTODY POSTS CRUD
# ================================
class ListCreateCustodyAPI(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        posts = SurrenderCustodyPet.objects.all().order_by('-updated_at')
        paginator = PostPagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = SurrenderPostListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = SurrenderCustodyPostSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, 201)
        return Response(serializer.errors, 400)


class RetrieveUpdateDeleteCustodyAPI(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        return SurrenderCustodyPet.objects.filter(pk=pk).first()

    def get(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return Response({"error": "Not Found"}, 404)
        return Response(SurrenderCustodyPostSerializer(post).data)

    def put(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return Response({"error": "Not Found"}, 404)
        
        updated_data = request.data.copy()
        updated_data["updated_at"] = timezone.now().isoformat()
        serializer = SurrenderCustodyPostSerializer(post, data=updated_data, partial=True, context={"request": request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, 400)

    def delete(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return Response({"error": "Not Found"}, 404)
        post.delete()
        return Response(status=204)
