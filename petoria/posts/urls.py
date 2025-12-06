# posts/urls.py
from django.urls import path

from .views import (
    LostPostListAPI,
    LostPostDetailAPI,
    FoundPostListAPI,
    FoundPostDetailAPI,
    SurrenderCustodyListAPI,
    SurrenderCustodyDetailAPI,
)

urlpatterns = [

    path("api/lost-posts/", LostPostListAPI.as_view(), name="lostpost-list-create"),
    path("api/lost-posts/<int:pk>/", LostPostDetailAPI.as_view(), name="lostpost-detail"),

    path("api/found-posts/", FoundPostListAPI.as_view(), name="foundpost-list-create"),
    path("api/found-posts/<int:pk>/", FoundPostDetailAPI.as_view(), name="foundpost-detail"),

    path("api/surrender-posts/", SurrenderCustodyListAPI.as_view(), name="surrenderpost-list-create"),
    path("api/surrender-posts/<int:pk>/", SurrenderCustodyDetailAPI.as_view(),
         name="surrenderpost-detail"),
]
