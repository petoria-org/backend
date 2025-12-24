from django.urls import path
from .views import (
    ListCreateSuccessStoryAPI,
    RetrieveUpdateDeleteSuccessStoryAPI,
    ListUserSuccessStoriesAPI,
    UploadSuccessStoryImageAPI,
    DeleteSuccessStoryImageAPI,
)

urlpatterns = [
    path("images/upload/", UploadSuccessStoryImageAPI.as_view(), name="success-story-image-upload"),
    path("images/<int:image_id>/", DeleteSuccessStoryImageAPI.as_view(), name="success-story-image-delete"),
    path("stories/", ListCreateSuccessStoryAPI.as_view(), name="list-create-success-stories"),
    path("user/stories/", ListUserSuccessStoriesAPI.as_view(), name="list-user-success-stories"),
    path("stories/<int:pk>/", RetrieveUpdateDeleteSuccessStoryAPI.as_view(), name="retrieve-update-delete-story"),
]
