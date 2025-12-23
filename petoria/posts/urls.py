# posts/urls.py
from django.urls import path

from .views import (
    ListCreateLostPostAPI,
    RetrieveUpdateDeleteLostPostAPI,
    ListCreateFoundPostAPI,
    RetrieveUpdateDeleteFoundPostAPI,
    ListCreateCustodyAPI,
    RetrieveUpdateDeleteCustodyAPI,
    ListAllPostsAPI,
    ListUserLostPostsAPI,
    ListUserFoundPostsAPI,
    ListUserCustodyPostsAPI,
    ListAllPostsUserAPI,
    UploadPostImageAPI,
    DeletePostImageAPI,
    FilterPostsAPI,
    SearchPostsAPI
)

urlpatterns = [
    path("images/upload/", UploadPostImageAPI.as_view(), name="post-image-upload"),
    path("images/<int:image_id>/", DeletePostImageAPI.as_view(), name="post-image-delete"),

    path("lost-posts/", ListCreateLostPostAPI.as_view(), name="lostpost-list-create"),
    path("lost-posts/<int:pk>/", RetrieveUpdateDeleteLostPostAPI.as_view(), name="lostpost-detail"),

    path("found-posts/", ListCreateFoundPostAPI.as_view(), name="foundpost-list-create"),
    path("found-posts/<int:pk>/", RetrieveUpdateDeleteFoundPostAPI.as_view(), name="foundpost-detail"),

    path("surrender-posts/", ListCreateCustodyAPI.as_view(), name="surrenderpost-list-create"),
    path("surrender-posts/<int:pk>/", RetrieveUpdateDeleteCustodyAPI.as_view(),
         name="surrenderpost-detail"),

    # All posts mixed feed
    path("all/", ListAllPostsAPI.as_view()),

    # User-specific posts
    path("user/lost/", ListUserLostPostsAPI.as_view()),
    path("user/found/", ListUserFoundPostsAPI.as_view()),
    path("user/surrender/", ListUserCustodyPostsAPI.as_view()),
    path("user/all/", ListAllPostsUserAPI.as_view()),

    path("filter/", FilterPostsAPI.as_view(), name="filter-posts"),
    path("search/", SearchPostsAPI.as_view(), name="search-posts"),

]
