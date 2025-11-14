from users.models import User
from .models import Chat
from .serializers import(
    GetOrCreateChatSerializer,
    MessageSerializer,
    ChatListSerializer,
)
from .paginations import ChatCursorPagination

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView


class GetOrCreatePrivateChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GetOrCreateChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user1 = request.user
        user2_id = serializer.validated_data["user_id"]

        # Ensure user2 exists
        try:
            user2 = User.objects.get(id=user2_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Prevent self-chat
        if user1.id == user2.id:
            return Response(
                {"error": "Cannot create chat with yourself"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create
        chat = Chat.get_or_create_private_chat(user1, user2)

        return Response(
            {"chat_id": chat.id},
            status=status.HTTP_200_OK
        )


class ChatMessagesAPIView(ListAPIView):
    serializer_class = MessageSerializer
    pagination_class = ChatCursorPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        chat_id = self.kwargs.get('chat_id')
        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            raise NotFound("Chat not found")
        
        # Optional: ensure the user is a participant
        if self.request.user not in chat.members.all():
            raise NotFound("You are not a member of this chat")

        # Messages are already ordered in pagination class
        return chat.messages.all()


class ChatListAPIView(ListAPIView):
    serializer_class = ChatListSerializer
    pagination_class = ChatCursorPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        return user.chats.all()