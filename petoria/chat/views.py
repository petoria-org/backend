from users.models import User
from .models import Chat, Message, Attachment
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import OuterRef, Subquery
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse
from .serializers import ChatSerializer, MessageSerializer, AttachmentSerializer
from .paginations import MessageCursorPagination, ChatCursorPagination
from .enums import AttachmentType

MAX_ATTACHMENT_SIZE = 20 * 1024 * 1024  # 20 MB
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}
ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-matroska",
}

# ------------------------------------------------------------
# ChatListAPI
# Returns the list of chats for the authenticated user
# ------------------------------------------------------------
class ChatListAPI(generics.ListAPIView):
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]
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
# ChatWithUserAPI
# Returns the chat id given user ids if exists
# else returns none
# ------------------------------------------------------------
class ChatWithUserAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        other_user_id = kwargs.get("user_id")

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


# ------------------------------------------------------------
# ChatMessagesListView
# Returns paginated messages for a chat
# ------------------------------------------------------------
class ChatMessagesListAPI(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
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
# AttachmentUploadView
# Upload an attachment (image/video/other) and return metadata
# ------------------------------------------------------------
class AttachmentUploadAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'error': 'missing_file'}, status=status.HTTP_400_BAD_REQUEST)

        content_type = (uploaded.content_type or '').lower()
        size = uploaded.size

        if size > MAX_ATTACHMENT_SIZE:
            return Response(
                {'error': 'file_too_large', 'max_bytes': MAX_ATTACHMENT_SIZE},
                status=status.HTTP_400_BAD_REQUEST
            )

        if content_type in ALLOWED_IMAGE_TYPES:
            attach_type = AttachmentType.IMAGE
        elif content_type in ALLOWED_VIDEO_TYPES:
            attach_type = AttachmentType.VIDEO
        else:
            return Response(
                {'error': 'unsupported_file_type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        attachment = Attachment.objects.create(
            uploaded_by=request.user,
            file=uploaded,
            content_type=content_type,
            size=size,
            type=attach_type,
        )

        serializer = AttachmentSerializer(attachment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ------------------------------------------------------------
# AttachmentDownloadView
# Download an attachment if the requester is a chat participant
# ------------------------------------------------------------
class AttachmentDownloadAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, attachment_id, *args, **kwargs):
        try:
            attachment = Attachment.objects.select_related(
                "message__chat"
            ).get(id=attachment_id)
        except Attachment.DoesNotExist:
            return Response({"error": "not_found"}, status=status.HTTP_404_NOT_FOUND)

        # ensure the attachment is bound to a message and user is in the chat
        if not attachment.message:
            return Response({"error": "unbound_attachment"}, status=status.HTTP_400_BAD_REQUEST)

        chat = attachment.message.chat
        if not chat.participants.filter(id=request.user.id).exists():
            return Response({"error": "not_in_chat"}, status=status.HTTP_403_FORBIDDEN)

        # stream the file
        try:
            file_handle = attachment.file.open("rb")
        except FileNotFoundError:
            return Response({"error": "file_missing"}, status=status.HTTP_404_NOT_FOUND)

        response = FileResponse(
            file_handle,
            content_type=attachment.content_type or "application/octet-stream",
        )
        response["Content-Length"] = attachment.size
        response["Content-Disposition"] = f'inline; filename="{attachment.file.name.split("/")[-1]}"'
        return response
