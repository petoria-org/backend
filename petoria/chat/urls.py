from django.urls import path
from .views import GetOrCreatePrivateChatView

urlpatterns = [
    path("get-or-create/", GetOrCreatePrivateChatView.as_view(), name="get_or_create_chat"),
]