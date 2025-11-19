from django.urls import path
from .views import (
    ChatListCreateAPIView,
    ChatDetailAPIView,
    ChatMessagesAPIView,
    MarkMessagesReadAPIView
)

urlpatterns = [
    path('chats/', ChatListCreateAPIView.as_view(), name='chat-list-create'),
    path('chats/<int:pk>/', ChatDetailAPIView.as_view(), name='chat-detail'),
    path('chats/<int:chat_pk>/messages/', ChatMessagesAPIView.as_view(), name='chat-messages'),
    path('chats/<int:chat_pk>/mark-read/', MarkMessagesReadAPIView.as_view(), name='chat-mark-read'),
]