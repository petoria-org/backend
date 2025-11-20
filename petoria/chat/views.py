from rest_framework import generics, permissions
from django.db.models import OuterRef, Subquery
from .models import Chat, Message, ChatParticipant
from .serializers import ChatSerializer, MessageSerializer

# ------------------------------------------------------------
# ChatListView
# Returns the list of chats for the authenticated user.
# ------------------------------------------------------------
class ChatListView(generics.ListAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Latest message subquery
        latest_msg = (
            Message.objects.filter(chat_id=OuterRef("pk")).order_by("-created_at")
        )

        return (
            Chat.objects.filter(participants=user)
            .select_related()
            .prefetch_related("participants")
            .annotate(
                last_message_id=Subquery(latest_msg.values("id")[:1]),
                last_message_content=Subquery(latest_msg.values("content")[:1]),
                last_message_created=Subquery(latest_msg.values("created_at")[:1]),
            )
            .order_by("-last_message_created")
        )


# ------------------------------------------------------------
# ChatMessagesListView
# Returns paginated messages for a chat.
# ------------------------------------------------------------
class ChatMessagesListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        chat_id = self.kwargs.get("chat_id")
        return (
            Message.objects.filter(chat_id=chat_id)
            .select_related("sender")
            .order_by("-created_at")  # newest first (pagination friendly)
        )
