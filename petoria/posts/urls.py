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
)

urlpatterns = [

    path("api/lost-posts/", ListCreateLostPostAPI.as_view(), name="lostpost-list-create"),
    path("api/lost-posts/<int:pk>/", RetrieveUpdateDeleteLostPostAPI.as_view(), name="lostpost-detail"),

    path("api/found-posts/", ListCreateFoundPostAPI.as_view(), name="foundpost-list-create"),
    path("api/found-posts/<int:pk>/", RetrieveUpdateDeleteFoundPostAPI.as_view(), name="foundpost-detail"),

    path("api/surrender-posts/", ListCreateCustodyAPI.as_view(), name="surrenderpost-list-create"),
    path("api/surrender-posts/<int:pk>/", RetrieveUpdateDeleteCustodyAPI.as_view(),
         name="surrenderpost-detail"),

    # All posts mixed feed
    path("all/", ListAllPostsAPI.as_view()),

    # User-specific posts
    path("User/lost/", ListUserLostPostsAPI.as_view()),
    path("User/found/", ListUserFoundPostsAPI.as_view()),
    path("User/surrender/", ListUserCustodyPostsAPI.as_view()),
    path("User/all/", ListAllPostsUserAPI.as_view()),
    ]
