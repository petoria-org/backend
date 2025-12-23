from rest_framework.pagination import CursorPagination
from django.db.models import Max, F
from django.db.models.functions import Coalesce

class MessageCursorPagination(CursorPagination):
    page_size = 50
    ordering = '-timestamp'
    cursor_query_param = 'cursor'

class ChatCursorPagination(CursorPagination):
    page_size = 20
    ordering = '-last_message_time'
    cursor_query_param = 'cursor'
    
    def paginate_queryset(self, queryset, request, view=None):
        queryset = queryset.annotate(
            last_message_time=Coalesce(
                Max('messages__timestamp'),
                F('created_at')
            )
        )
        return super().paginate_queryset(queryset, request, view)
