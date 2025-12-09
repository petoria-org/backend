from typing import Any, List, Dict

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Lost_post, Found_post, Surrender_custody_pets
from .pagination import PostPagination
from .serializers import LostPostSerializer, FoundPostSerializer, SurrenderCustodyPostSerializer


class AllPosts(APIView):

    def get(self, request, *args: Any, **kwargs: Any) -> Response:
        lost = Lost_post.objects.all().order_by("-created_at")
        found = Found_post.objects.all().order_by("-created_at")
        surrender = Surrender_custody_pets.objects.all().order_by("-created_at")

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


class UserLostPostsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args: Any, **kwargs: Any) -> Response:
        posts = Lost_post.objects.filter(user=request.user).order_by("-created_at")
        paginator = PostPagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = LostPostSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class UserFoundPostsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args: Any, **kwargs: Any) -> Response:
        posts = Found_post.objects.filter(user=request.user).order_by("-created_at")
        paginator = PostPagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = FoundPostSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class UserSurrenderPostsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args: Any, **kwargs: Any) -> Response:
        posts = Surrender_custody_pets.objects.filter(user=request.user).order_by("-created_at")
        paginator = PostPagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = SurrenderCustodyPostSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AllPostsUser(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args: Any, **kwargs: Any) -> Response:
        user = request.user

        lost = Lost_post.objects.filter(user=user)
        found = Found_post.objects.filter(user=user)
        surrender = Surrender_custody_pets.objects.filter(user=user)

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
class LostPostListAPI(APIView):
    def get(self, request):
        posts = Lost_post.objects.all().order_by('-created_at')

        paginator = PostPagination()
        result_page = paginator.paginate_queryset(posts, request)

        serializer = LostPostSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = LostPostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


# RETRIEVE + UPDATE + DELETE
class LostPostDetailAPI(APIView):
    def get_object(self, pk):
        try:
            return Lost_post.objects.get(pk=pk)
        except Lost_post.DoesNotExist:
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


class FoundPostListAPI(APIView):
    def get(self, request):
        posts = Found_post.objects.all().order_by('-created_at')

        paginator = PostPagination()
        result_page = paginator.paginate_queryset(posts, request)

        serializer = FoundPostSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = FoundPostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class FoundPostDetailAPI(APIView):
    def get_object(self, pk):
        try:
            return Found_post.objects.get(pk=pk)
        except Found_post.DoesNotExist:
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


class SurrenderCustodyListAPI(APIView):
    def get(self, request):
        posts = Surrender_custody_pets.objects.all().order_by('-created_at')

        paginator = PostPagination()
        result_page = paginator.paginate_queryset(posts, request)

        serializer = SurrenderCustodyPostSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = SurrenderCustodyPostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class SurrenderCustodyDetailAPI(APIView):
    def get_object(self, pk):
        try:
            return Surrender_custody_pets.objects.get(pk=pk)
        except Surrender_custody_pets.DoesNotExist:
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
