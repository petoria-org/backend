from django.contrib import admin
from .models import Chat, Message
# Register your models here.

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['id', 'is_private', 'created_at']
    filter_horizontal = ['members']   # clean multi-select UI
    
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    pass
