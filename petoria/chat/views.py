from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from users.models import User
from .models import Chat
from .serializers import GetOrCreateChatSerializer


class GetOrCreatePrivateChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GetOrCreateChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user1 = request.user
        user2_id = serializer.validated_data["other_user_id"]

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
