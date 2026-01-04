from django.contrib import admin
from .models import ChatParticipant, Chat, Message

# Register your models here.
admin.site.register(ChatParticipant)
admin.site.register(Chat)
admin.site.register(Message)
