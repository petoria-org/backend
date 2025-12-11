from django.urls import path
from .views import (
    ListCreateSuccessStoryAPI,
    RetrieveUpdateDeleteSuccessStoryAPI,
    ListAllSuccessStoriesAPI,
)

urlpatterns = [
    # نمایش همه داستان‌ها (عمومی)
    path("stories/", ListAllSuccessStoriesAPI.as_view(), name="list-all-success-stories"),

    # لیست و ایجاد داستان توسط کاربر
    path("user/stories/", ListCreateSuccessStoryAPI.as_view(), name="list-create-user-stories"),

    # مشاهده، ویرایش، حذف داستان
    path("stories/<int:pk>/", RetrieveUpdateDeleteSuccessStoryAPI.as_view(), name="retrieve-update-delete-story"),
]
