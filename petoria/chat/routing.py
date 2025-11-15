from django.urls import re_path
from .consumers import UserChatsConsumer

websocket_urlpatterns = [
    re_path(r"ws/chats/$", UserChatsConsumer.as_asgi()),
]
