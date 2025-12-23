from rest_framework import viewsets, filters
from .models import Location
from .serializers import LocationSerializer

class LocationViewSet(viewsets.ModelViewSet):
    """
    API برای مدیریت لوکیشن‌ها
    امکان ثبت آدرس جدید (POST) و مشاهده لیست (GET)
    """
    queryset = Location.objects.all().order_by('-id')
    serializer_class = LocationSerializer
    
    # اضافه کردن قابلیت جستجو بر اساس شهر یا منطقه در URL
    filter_backends = [filters.SearchFilter]
    search_fields = ['city', 'district', 'full_address']

    # اگر بعداً خواستید فقط آگهی‌های یک شهر خاص را بگیرید:
    def get_queryset(self):
        queryset = Location.objects.all()
        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)
        return queryset