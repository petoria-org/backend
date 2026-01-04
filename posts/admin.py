from django.contrib import admin
from .models import LostPost, FoundPost, SurrenderCustodyPet

# Register your models here.
admin.site.register(LostPost)
admin.site.register(FoundPost)
admin.site.register(SurrenderCustodyPet)
