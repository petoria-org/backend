from rest_framework.pagination import CursorPagination

NUMBER_OF_MESSAGES_TO_LOAD_AT_ONCE = 50

class ChatCursorPagination(CursorPagination):
    page_size = NUMBER_OF_MESSAGES_TO_LOAD_AT_ONCE
    ordering = '-timestamp'
    cursor_query_param = 'cursor'
