from django.urls import path
from .views import (
    ListCreateSuccessStoryAPI,
    RetrieveUpdateDeleteSuccessStoryAPI,
    ListAllSuccessStoriesAPI,
)

urlpatterns = [
    path("stories/", ListAllSuccessStoriesAPI.as_view(), name="list-all-success-stories"),
    path("user/stories/", ListCreateSuccessStoryAPI.as_view(), name="list-create-user-stories"),
    path("stories/<int:pk>/", RetrieveUpdateDeleteSuccessStoryAPI.as_view(), name="retrieve-update-delete-story"),
]
