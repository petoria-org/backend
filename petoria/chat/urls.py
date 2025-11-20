from django.urls import path
from .views import (
    ChatListView,
    ChatMessagesListView,
)

urlpatterns = [
    path('chats/', ChatListView.as_view(), name='chat-list'),
    path('chats/<int:chat_pk>/messages/', ChatMessagesListView.as_view(), name='chat-messages'),
]
