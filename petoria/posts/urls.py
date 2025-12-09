# posts/urls.py
from django.urls import path

from .views import (
    LostPostListAPI,
    LostPostDetailAPI,
    FoundPostListAPI,
    FoundPostDetailAPI,
    SurrenderCustodyListAPI,
    SurrenderCustodyDetailAPI,
    AllPosts,
    UserLostPostsAPI,
    UserFoundPostsAPI,
    UserSurrenderPostsAPI,
    AllPostsUser,
)

urlpatterns = [

    path("api/lost-posts/", LostPostListAPI.as_view(), name="lostpost-list-create"),
    path("api/lost-posts/<int:pk>/", LostPostDetailAPI.as_view(), name="lostpost-detail"),

    path("api/found-posts/", FoundPostListAPI.as_view(), name="foundpost-list-create"),
    path("api/found-posts/<int:pk>/", FoundPostDetailAPI.as_view(), name="foundpost-detail"),

    path("api/surrender-posts/", SurrenderCustodyListAPI.as_view(), name="surrenderpost-list-create"),
    path("api/surrender-posts/<int:pk>/", SurrenderCustodyDetailAPI.as_view(),
         name="surrenderpost-detail"),

    # All posts mixed feed
    path("all/", AllPosts.as_view()),

    # User-specific posts
    path("User/lost/", UserLostPostsAPI.as_view()),
    path("User/found/", UserFoundPostsAPI.as_view()),
    path("User/surrender/", UserSurrenderPostsAPI.as_view()),
    path("User/all/", AllPostsUser.as_view()),
    ]
