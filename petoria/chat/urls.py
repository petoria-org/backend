from django.urls import path
from .views import(
    GetOrCreatePrivateChatView,
    ChatMessagesAPIView,
    ChatListAPIView
)

urlpatterns = [
    
    path(
        "get-or-create/",
        GetOrCreatePrivateChatView.as_view(),
        name="get_or_create_chat"
    ),
    
    path(
        'messages/<int:chat_id>/',
        ChatMessagesAPIView.as_view(),
        name='chat-messages'
    ),
    path(
        'my-chats/',
        ChatListAPIView.as_view(),
    )    
]