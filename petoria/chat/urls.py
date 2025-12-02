from django.urls import path
from .views import (
    ChatListView,
    ChatMessagesListView,
    ChatWithUserAPIView,
    AttachmentUploadView,
)

urlpatterns = [
    path('list/', ChatListView.as_view(), name='chat-list'),
    path('messages/<int:chat_pk>/', ChatMessagesListView.as_view(), name='chat-messages'),
    path("with/", ChatWithUserAPIView.as_view(), name="chat-with-user"),
    path('attachments/upload/', AttachmentUploadView.as_view(), name='chat-attachment-upload'),
]
