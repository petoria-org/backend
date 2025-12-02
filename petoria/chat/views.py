from users.models import User
from .models import Chat, Message
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import OuterRef, Subquery
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from .serializers import ChatSerializer, MessageSerializer
from .paginations import MessageCursorPagination, ChatCursorPagination

# ------------------------------------------------------------
# ChatListView
# Returns the list of chats for the authenticated user
# ------------------------------------------------------------
class ChatListView(generics.ListAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ChatCursorPagination

    def get_queryset(self):
        user = self.request.user

        # Latest message subquery
        latest_msg = (
            Message.objects.filter(chat_id=OuterRef("pk")).order_by("-timestamp")
        )

        return (
            Chat.objects.filter(participants=user)
            .select_related()
            .prefetch_related("participants")
            .annotate(
                last_message_id=Subquery(latest_msg.values("id")[:1]),
                last_message_content=Subquery(latest_msg.values("content")[:1]),
                last_message_created=Subquery(latest_msg.values("timestamp")[:1]),
                last_message_sender_id=Subquery(latest_msg.values("sender_id")[:1]),
                last_message_sender_name=Subquery(latest_msg.values("sender__username")[:1]),
                last_message_is_read=Subquery(latest_msg.values("is_read")[:1]),
            )
            .order_by("-last_message_created")
        )

# ------------------------------------------------------------
# ChatMessagesListView
# Returns paginated messages for a chat
# ------------------------------------------------------------
class ChatMessagesListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MessageCursorPagination

    def get_queryset(self):
        chat_id = self.kwargs.get("chat_pk")

        # ensure requester is a participant
        if not Chat.objects.filter(id=chat_id, participants=self.request.user).exists():
            raise PermissionDenied("not_in_chat")
        return (
            Message.objects.filter(chat_id=chat_id)
            .select_related("sender")
            .order_by("-timestamp")  # newest first (pagination friendly)
        )

# ------------------------------------------------------------
# ChatWithUserAPIView
# Returns the chat id given user ids if exists
# else returns none
# ------------------------------------------------------------
class ChatWithUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        other_user_id = request.query_params.get("user_id")

        if not other_user_id:
            return Response(
                {"error": "missing_user_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if str(other_user_id) == str(request.user.id):
            return Response(
                {"error": "cannot_chat_with_self"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # validate other user
        try:
            other_user = User.objects.get(id=other_user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "user_not_found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # find chat if exists
        chat = Chat.get_chat_between(request.user, other_user)

        return Response({
            "chat_id": chat.id if chat else None
        })
