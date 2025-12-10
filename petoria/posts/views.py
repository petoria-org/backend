from typing import Any, List, Dict

from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LostPost, FoundPost, SurrenderCustodyPet
from .pagination import PostPagination
from .serializers import LostPostSerializer, FoundPostSerializer, SurrenderCustodyPostSerializer

class ListAllPostsUserAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args: Any, **kwargs: Any) -> Response:
        user = request.user

        lost = LostPost.objects.filter(user=user)
        found = FoundPost.objects.filter(user=user)
        surrender = SurrenderCustodyPet.objects.filter(user=user)

        combined: List[Dict[str, Any]] = []

        for obj in lost:
            data = LostPostSerializer(obj).data
            data["type"] = "lost"
            combined.append(data)

        for obj in found:
            data = FoundPostSerializer(obj).data
            data["type"] = "found"
            combined.append(data)

        for obj in surrender:
            data = SurrenderCustodyPostSerializer(obj).data
            data["type"] = "surrender"
            combined.append(data)

        combined = sorted(combined, key=lambda x: x["created_at"], reverse=True)

        paginator = PostPagination()
        page = paginator.paginate_queryset(combined, request)
        return paginator.get_paginated_response(page)
    

class ListUserLostPostsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args: Any, **kwargs: Any) -> Response:
        posts = LostPost.objects.filter(user=request.user).order_by("-created_at")
        paginator = PostPagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = LostPostSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ListUserFoundPostsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args: Any, **kwargs: Any) -> Response:
        posts = FoundPost.objects.filter(user=request.user).order_by("-created_at")
        paginator = PostPagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = FoundPostSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ListUserCustodyPostsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args: Any, **kwargs: Any) -> Response:
        posts = SurrenderCustodyPet.objects.filter(user=request.user).order_by("-created_at")
        paginator = PostPagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = SurrenderCustodyPostSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ListAllPostsAPI(APIView):
    permission_classes = [AllowAny]
    def get(self, request, *args: Any, **kwargs: Any) -> Response:
        lost = LostPost.objects.all().order_by("-created_at")
        found = FoundPost.objects.all().order_by("-created_at")
        surrender = SurrenderCustodyPet.objects.all().order_by("-created_at")

        combined: List[Dict[str, Any]] = []

        for obj in lost:
            data = LostPostSerializer(obj).data
            data["type"] = "lost"
            combined.append(data)

        for obj in found:
            data = FoundPostSerializer(obj).data
            data["type"] = "found"
            combined.append(data)

        for obj in surrender:
            data = SurrenderCustodyPostSerializer(obj).data
            data["type"] = "surrender"
            combined.append(data)

        combined = sorted(combined, key=lambda x: x["created_at"], reverse=True)

        paginator = PostPagination()
        page = paginator.paginate_queryset(combined, request)
        return paginator.get_paginated_response(page)

# LIST + CREATE
class ListCreateLostPostAPI(APIView):
    # Anyone can list; POST requires auth via IsAuthenticatedOrReadOnly
    permission_classes = [IsAuthenticatedOrReadOnly]
    def get(self, request):
        posts = LostPost.objects.all().order_by('-created_at')

        paginator = PostPagination()
        result_page = paginator.paginate_queryset(posts, request)

        serializer = LostPostSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = LostPostSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


# RETRIEVE + UPDATE + DELETE
class RetrieveUpdateDeleteLostPostAPI(APIView):
    permission_classes = [AllowAny]
    def get_object(self, pk):
        try:
            return LostPost.objects.get(pk=pk)
        except LostPost.DoesNotExist:
            return None

    def get(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return Response({"error": "Not Found"}, status=404)
        serializer = LostPostSerializer(post)
        return Response(serializer.data)

    def put(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return Response({"error": "Not Found"}, status=404)
        serializer = LostPostSerializer(post, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return Response({"error": "Not Found"}, status=404)
        post.delete()
        return Response(status=204)


class ListCreateFoundPostAPI(APIView):
    permission_classes=[IsAuthenticatedOrReadOnly]
    def get(self, request):
        posts = FoundPost.objects.all().order_by('-created_at')

        paginator = PostPagination()
        result_page = paginator.paginate_queryset(posts, request)

        serializer = FoundPostSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = FoundPostSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class RetrieveUpdateDeleteFoundPostAPI(APIView):
    permission_classes = [AllowAny]
    def get_object(self, pk):
        try:
            return FoundPost.objects.get(pk=pk)
        except FoundPost.DoesNotExist:
            return None

    def get(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return Response({"error": "Not Found"}, status=404)
        serializer = FoundPostSerializer(post)
        return Response(serializer.data)

    def put(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return Response({"error": "Not Found"}, status=404)
        serializer = FoundPostSerializer(post, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return Response({"error": "Not Found"}, status=404)
        post.delete()
        return Response(status=204)


class ListCreateCustodyAPI(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    def get(self, request):
        posts = SurrenderCustodyPet.objects.all().order_by('-created_at')

        paginator = PostPagination()
        result_page = paginator.paginate_queryset(posts, request)

        serializer = SurrenderCustodyPostSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = SurrenderCustodyPostSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class RetrieveUpdateDeleteCustodyAPI(APIView):
    permission_classes = [AllowAny]
    def get_object(self, pk):
        try:
            return SurrenderCustodyPet.objects.get(pk=pk)
        except SurrenderCustodyPet.DoesNotExist:
            return None

    def get(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return Response({"error": "Not Found"}, status=404)
        serializer = SurrenderCustodyPostSerializer(post)
        return Response(serializer.data)

    def put(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return Response({"error": "Not Found"}, status=404)
        serializer = SurrenderCustodyPostSerializer(post, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        post = self.get_object(pk)
        if not post:
            return Response({"error": "Not Found"}, status=404)
        post.delete()
        return Response(status=204)
