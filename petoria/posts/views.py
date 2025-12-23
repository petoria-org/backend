from typing import Any, List, Dict

from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LostPost, FoundPost, SurrenderCustodyPet
from .models import LostPost, FoundPost, SurrenderCustodyPet
from .models import PostImage
from .pagination import PostPagination
from .serializers import (
    LostPostListSerializer, FoundPostListSerializer, SurrenderPostListSerializer
)
from .serializers import (
    LostPostSerializer, FoundPostSerializer, SurrenderCustodyPostSerializer,
    PostImageSerializer
)


class FilterPostsAPI(APIView):
    """
    Unified API for filtering all post types (lost, found, adoption).
    Filters:
        - pet_type, pet_sex, city
        - pet_age_range (under_1, 1_2, 2_3, 3_5, 5_7)
        - has_birth_certificate, vaccination, steriliz (for adoption posts)
    """

    permission_classes = [AllowAny]

    # ===============================
    # filter Lost & Found
    # ===============================
    def filter_lost_found(self, queryset, params):
        pet_type = params.get("pet_type")
        pet_sex = params.get("pet_sex")
        city = params.get("city")
        age_range = params.get("pet_age_range")

        if pet_type:
            queryset = queryset.filter(pet_type=pet_type)
        if pet_sex:
            queryset = queryset.filter(pet_sex=pet_sex)
        if city and city.lower() != "all":
            queryset = queryset.filter(location__city__icontains=city)
        if age_range:
            queryset = self.filter_age(queryset, age_range)
        return queryset

    # ===============================
    # filter Surrender
    # ===============================
    def filter_surrender(self, queryset, params):
        queryset = self.filter_lost_found(queryset, params)
        passport = params.get("has_birth_certificate")
        vaccination = params.get("vaccination")
        steriliz = params.get("steriliz")

        if passport is not None:
            queryset = queryset.filter(has_birth_certificate=(passport.lower() == "true"))
        if vaccination is not None:
            queryset = queryset.filter(vaccination=(vaccination.lower() == "true"))
        if steriliz is not None:
            queryset = queryset.filter(steriliz=(steriliz.lower() == "true"))
        return queryset

    # ===============================
    # age range filtering
    # ===============================
    def filter_age(self, queryset, age_range):
        """
        age_range values from front-end:
        under_1, 1_2, 2_3, 3_5, 5_7
        """

        if age_range == "under_1":
            return queryset.filter(pet_age__icontains="0")
        elif age_range == "1_2":
            return queryset.filter(pet_age__regex=r"^1(\.|$)|2(\.|$)")
        elif age_range == "2_3":
            return queryset.filter(pet_age__regex=r"^2(\.|$)|3(\.|$)")
        elif age_range == "3_5":
            return queryset.filter(pet_age__regex=r"^3(\.|$)|4(\.|$)|5(\.|$)")
        elif age_range == "5_7":
            return queryset.filter(pet_age__regex=r"^5(\.|$)|6(\.|$)|7(\.|$)")
        return queryset

    # ===============================
    # GET method
    # ===============================
    def get(self, request):
        params = request.query_params

        # --- Lost Posts ---
        lost_qs = self.filter_lost_found(LostPost.objects.all().order_by("-created_at"), params)
        lost_serialized = LostPostListSerializer(lost_qs, many=True).data
        for item in lost_serialized:
            item["type"] = "lost"

        # --- Found Posts ---
        found_qs = self.filter_lost_found(FoundPost.objects.all().order_by("-created_at"), params)
        found_serialized = FoundPostListSerializer(found_qs, many=True).data
        for item in found_serialized:
            item["type"] = "found"

        # --- Surrender / Adoption ---
        surrender_qs = self.filter_surrender(SurrenderCustodyPet.objects.all().order_by("-created_at"), params)
        surrender_serialized = SurrenderPostListSerializer(surrender_qs, many=True).data
        for item in surrender_serialized:
            item["type"] = "surrender"

        # Combine all
        combined = lost_serialized + found_serialized + surrender_serialized
        combined.sort(key=lambda x: x["created_at"], reverse=True)

        paginator = PostPagination()
        page = paginator.paginate_queryset(combined, request)
        return paginator.get_paginated_response(page)


# ================================
#   POST IMAGES UPLOAD
# ================================
class UploadPostImageAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        uploaded = request.FILES.get("image")
        if not uploaded:
            return Response({"error": "No image provided."}, status=400)

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

        combined.sort(key=lambda x: x["created_at"], reverse=True)

        paginator = PostPagination()
        page = paginator.paginate_queryset(combined, request)
        return paginator.get_paginated_response(page)


# ================================
#   USER POSTS (SEPARATE)
# ================================
class ListUserLostPostsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        posts = LostPost.objects.filter(user=request.user).order_by("-created_at")
        paginator = PostPagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = LostPostListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ListUserFoundPostsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        posts = FoundPost.objects.filter(user=request.user).order_by("-created_at")
        paginator = PostPagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = FoundPostListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ListUserCustodyPostsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        posts = SurrenderCustodyPet.objects.filter(user=request.user).order_by("-created_at")
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
        lost = LostPost.objects.all().order_by("-created_at")
        found = FoundPost.objects.all().order_by("-created_at")
        surrender = SurrenderCustodyPet.objects.all().order_by("-created_at")

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

        combined.sort(key=lambda x: x["created_at"], reverse=True)

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

        serializer = LostPostSerializer(post, data=request.data, partial=True, context={"request": request})
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
        posts = FoundPost.objects.all().order_by('-created_at')
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

        serializer = FoundPostSerializer(post, data=request.data, partial=True, context={"request": request})
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
        posts = SurrenderCustodyPet.objects.all().order_by('-created_at')
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

        serializer = SurrenderCustodyPostSerializer(post, data=request.data, partial=True, context={"request": request})
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
