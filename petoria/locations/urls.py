from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LocationViewSet

# ساخت یک روتر و ثبت ویوست
router = DefaultRouter()
router.register(r'locations', LocationViewSet, basename='location')

urlpatterns = [
    path('', include(router.urls)),
]