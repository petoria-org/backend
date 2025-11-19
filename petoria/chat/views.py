from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import transaction, models
from django.db.models import Max, F, Count
from django.db.models.functions import Coalesce
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from users.models import User
from .models import Chat, Message, ChatParticipant
from .serializers import ChatSerializer, MessageSerializer, CreateChatSerializer
from .paginations import MessageCursorPagination, ChatCursorPagination

class ChatListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        queryset = Chat.objects.filter(
            participants=request.user
        ).annotate(
            participant_count=Count('participants')
        ).filter(
            participant_count=2
        ).prefetch_related(
            'participants', 
            'participants_info'
        ).annotate(
            last_message_time=Coalesce(
                Max('messages__timestamp'),
                F('created_at')
            )
        ).order_by('-last_message_time')
        
        paginator = ChatCursorPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = ChatSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)
        
        serializer = ChatSerializer(queryset, many=True, context={'request': request})
        return Response({'chats': serializer.data})
    
    def post(self, request):
        serializer = CreateChatSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        other_user = User.objects.get(id=data['other_user_id'])
        existing_chat = Chat.get_chat_between(request.user, other_user)
        
        if existing_chat:
            return Response(
                ChatSerializer(existing_chat, context={'request': request}).data,
                status=status.HTTP_200_OK
            )
        
        with transaction.atomic():
            chat = Chat.objects.create()
            chat.participants.add(request.user, other_user)
            message = Message.objects.create(
                chat=chat,
                sender=request.user,
                content=data['message']
            )
        
        self._notify_new_chat(other_user, chat, message)
        
        return Response(
            ChatSerializer(chat, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    def _notify_new_chat(self, other_user, chat, message):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{other_user.id}",
            {
                'type': 'new_chat_notification',
                'chat': {
                    'id': chat.id,
                    'other_participant': {
                        'id': self.request.user.id,
                        'username': self.request.user.username
                    },
                    'last_message': {
                        'id': message.id,
                        'sender_id': self.request.user.id,
                        'sender_name': self.request.user.username,
                        'content': message.content[:150],
                        'timestamp': message.timestamp.isoformat()
                    },
                    'unread_count': 1
                }
            }
        )

class ChatDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        try:
            chat = Chat.objects.get(pk=pk)
        except Chat.DoesNotExist:
            return Response({'error': 'Chat not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user not in chat.participants.all():
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        if chat.participants.count() != 2:
            return Response({'error': 'Invalid chat type'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ChatSerializer(chat, context={'request': request})
        return Response(serializer.data)

class ChatMessagesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, chat_pk):
        try:
            chat = Chat.objects.get(pk=chat_pk)
        except Chat.DoesNotExist:
            return Response({'error': 'Chat not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user not in chat.participants.all():
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        messages_queryset = chat.messages.select_related('sender').all()
        paginator = MessageCursorPagination()
        page = paginator.paginate_queryset(messages_queryset, request)
        
        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = MessageSerializer(messages_queryset, many=True)
        return Response({'messages': serializer.data})

class MarkMessagesReadAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, chat_pk):
        try:
            chat = Chat.objects.get(pk=chat_pk)
        except Chat.DoesNotExist:
            return Response({'error': 'Chat not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user not in chat.participants.all():
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        message_ids = list(Message.objects.filter(
            chat=chat,
            is_read=False
        ).exclude(sender=request.user).values_list('id', flat=True))
        
        Message.objects.filter(id__in=message_ids).update(is_read=True)
        ChatParticipant.objects.filter(
            chat=chat, user=request.user
        ).update(unread_count=0)
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{chat_pk}",
            {
                'type': 'read_receipt',
                'reader_id': request.user.id,
                'reader_name': request.user.username,
                'message_ids': message_ids
            }
        )
        
        return Response({
            'status': 'marked read',
            'count': len(message_ids)
        })