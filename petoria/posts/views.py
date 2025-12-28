from typing import Any, List, Dict, Optional

from django.db.models import Case, IntegerField, Q, Value, When
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


def _parse_bool_param(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    return None


def _parse_bool_list(values: List[str]) -> Optional[set]:
    parsed = set()
    for value in values:
        parsed_value = _parse_bool_param(value)
        if parsed_value is not None:
            parsed.add(parsed_value)
    return parsed or None


def _split_list_param(params, key: str) -> List[str]:
    raw = params.get(key, "")
    if not raw:
        return []
    values: List[str] = []
    for item in raw.split(","):
        item = item.strip()
        if item:
            values.append(item)
    return values


def _age_range_q(age_range: str) -> Optional[Q]:
    if age_range == "under_1":
        return Q(pet_age__years=0)
    if age_range == "1_2":
        return Q(pet_age__years=1)
    if age_range == "2_3":
        return Q(pet_age__years=2)
    if age_range == "3_5":
        return Q(pet_age__years__in=[3, 4])
    if age_range == "5_7":
        return Q(pet_age__years__in=[5, 6])
    if age_range in {"over_7"}:
        return Q(pet_age__years__gte=7)
    return None


def _filter_age_ranges(queryset, age_ranges: List[str]):
    combined_q = Q()
    has_ranges = False
    for age_range in age_ranges:
        range_q = _age_range_q(age_range)
        if range_q is not None:
            combined_q |= range_q
            has_ranges = True
    if has_ranges:
        return queryset.filter(combined_q)
    return queryset


MALE_TERMS = {"male", "مرد", "پسر", "نر"}
FEMALE_TERMS = {"female", "زن", "دختر", "ماده"}


def _apply_search(queryset, params, include_diseases: bool = False):
    query = (params.get("q") or "").strip()
    if not query:
        return queryset

    terms = [term for term in query.split() if term]
    if not terms:
        return queryset

    fields = [
        "title",
        "description",
        "pet_name",
        "breed",
        "Specific_symptoms",
        "location__city",
    ]
    if include_diseases:
        fields.append("diseases")

    term_qs: List[Q] = []
    for term in terms:
        term_q = Q()
        term_lower = term.lower()
        for field in fields:
            term_q |= Q(**{f"{field}__icontains": term})
        if term_lower in MALE_TERMS:
            term_q |= Q(pet_sex="male")
        elif term_lower in FEMALE_TERMS:
            term_q |= Q(pet_sex="female")
        age_range_q = _age_range_q(term_lower)
        if age_range_q is not None:
            term_q |= age_range_q
        if term.isdigit():
            age_value = int(term)
            term_q |= Q(pet_age__years=age_value) | Q(pet_age__months=age_value)
        term_qs.append(term_q)

    if not term_qs:
        return queryset

    if len(term_qs) == 1:
        return queryset.filter(term_qs[0])

    if len(term_qs) <= 2:
        min_match = len(term_qs)
    elif len(term_qs) <= 4:
        min_match = 3
    else:
        min_match = 4

    match_count = sum(
        (
            Case(
                When(term_q, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
            for term_q in term_qs
        ),
        Value(0),
    )
    return queryset.annotate(_search_match_count=match_count).filter(
        _search_match_count__gte=min_match
    )


def _apply_common_filters(queryset, params):
    pet_types = _split_list_param(params, "pet_type")
    pet_sexes = _split_list_param(params, "pet_sex")
    cities = _split_list_param(params, "city")
    age_ranges = _split_list_param(params, "pet_age_range")

    if pet_types:
        queryset = queryset.filter(pet_type__in=pet_types)
    if pet_sexes:
        queryset = queryset.filter(pet_sex__in=pet_sexes)
    if cities:
        if not any(city.lower() == "all" for city in cities):
            city_q = Q()
            for city in cities:
                city_q |= Q(location__city__iexact=city)
            queryset = queryset.filter(city_q)
    if age_ranges:
        queryset = _filter_age_ranges(queryset, age_ranges)
    return queryset


def _apply_surrender_filters(queryset, params):
    steriliz_values = _parse_bool_list(_split_list_param(params, "steriliz"))
    vaccination_values = _parse_bool_list(_split_list_param(params, "vaccination"))
    birth_certificate_values = _parse_bool_list(_split_list_param(params, "has_birth_certificate"))

    if steriliz_values == {True}:
        queryset = queryset.filter(steriliz=True)
    elif steriliz_values == {False}:
        queryset = queryset.filter(steriliz=False)
    if vaccination_values == {True}:
        queryset = queryset.filter(vaccination=True)
    elif vaccination_values == {False}:
        queryset = queryset.filter(vaccination=False)
    if birth_certificate_values == {True}:
        queryset = queryset.filter(has_birth_certificate=True)
    elif birth_certificate_values == {False}:
        queryset = queryset.filter(has_birth_certificate=False)
    return queryset


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
        allowed_types = {"image/jpeg", "image/png", "image/webp"}
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
        params = request.query_params
        lost = _apply_common_filters(
            _apply_search(
                LostPost.objects.all().order_by("-updated_at"),
                params,
            ),
            params,
        )
        found = _apply_common_filters(
            _apply_search(
                FoundPost.objects.all().order_by("-updated_at"),
                params,
            ),
            params,
        )
        surrender = _apply_common_filters(
            _apply_search(
                SurrenderCustodyPet.objects.all().order_by("-updated_at"),
                params,
                include_diseases=True,
            ),
            params,
        )
        surrender = _apply_surrender_filters(surrender, params)

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
        posts = _apply_common_filters(
            _apply_search(
                LostPost.objects.all().order_by("-created_at"),
                request.query_params,
            ),
            request.query_params,
        )
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
        if request.user != post.user:
            return Response({"error": "Not permitted to edit this post"}, status=403)

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
        if request.user != post.user:
            return Response({"error": "Not permitted to edit this post"}, status=403)
        post.delete()
        return Response(status=204)


# ================================
#   FOUND POSTS CRUD
# ================================
class ListCreateFoundPostAPI(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        posts = _apply_common_filters(
            _apply_search(
                FoundPost.objects.all().order_by("-updated_at"),
                request.query_params,
            ),
            request.query_params,
        )
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
        if request.user != post.user:
            return Response({"error": "Not permitted to edit this post"}, status=403)

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
        if request.user != post.user:
            return Response({"error": "Not permitted to edit this post"}, status=403)
        post.delete()
        return Response(status=204)


# ================================
#   CUSTODY POSTS CRUD
# ================================
class ListCreateCustodyAPI(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        posts = _apply_common_filters(
            _apply_search(
                SurrenderCustodyPet.objects.all().order_by("-updated_at"),
                request.query_params,
                include_diseases=True,
            ),
            request.query_params,
        )
        posts = _apply_surrender_filters(posts, request.query_params)
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
        
        if request.user != post.user:
            return Response({"error": "Not permitted to edit this post"}, status=403)
        
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
        
        if request.user != post.user:
            return Response({"error": "Not permitted to edit this post"}, status=403)
        
        post.delete()
        return Response(status=204)
