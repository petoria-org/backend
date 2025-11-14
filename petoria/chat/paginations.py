from rest_framework.pagination import CursorPagination

NUMBER_OF_MESSAGES_TO_LOAD_AT_ONCE = 50

class MessageCursorPagination(CursorPagination):
    page_size = NUMBER_OF_MESSAGES_TO_LOAD_AT_ONCE
    ordering = '-timestamp'
    cursor_query_param = 'cursor'

class ChatCursorPagination(CursorPagination):
    page_size = NUMBER_OF_MESSAGES_TO_LOAD_AT_ONCE
    ordering = 'created_at'
    cursor_query_param = 'cursor'
