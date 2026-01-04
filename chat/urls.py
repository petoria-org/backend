from django.urls import path
from .views import (
    ChatListAPI,
    ChatMessagesListAPI,
    ChatWithUserAPI,
    AttachmentUploadAPI,
    AttachmentDownloadAPI,
)

urlpatterns = [
    path('list/', ChatListAPI.as_view(), name='chat-list'),
    path('messages/<int:chat_pk>/', ChatMessagesListAPI.as_view(), name='chat-messages'),
    path("with/<int:user_id>/", ChatWithUserAPI.as_view(), name="chat-with-user"),
    path('attachments/upload/', AttachmentUploadAPI.as_view(), name='chat-attachment-upload'),
    path('attachments/<int:attachment_id>/download/', AttachmentDownloadAPI.as_view(), name='chat-attachment-download'),
]
