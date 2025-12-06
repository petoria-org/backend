from django.contrib import admin
from .models import Lost_post, Found_post, Surrender_custody_pets

# Register your models here.
admin.site.register(Lost_post)
admin.site.register(Found_post)
admin.site.register(Surrender_custody_pets)
