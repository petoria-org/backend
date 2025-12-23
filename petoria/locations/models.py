from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.core.cache import cache
import requests

class Location(models.Model):
    country = models.CharField(max_length=150, blank=True, null=True, default="ایران")
    city = models.CharField(max_length=150, blank=True, null=True)
    district = models.CharField(max_length=150, blank=True, null=True)
    full_address = models.TextField(blank=True, null=True) # اضافه شده برای UX بهتر
    point = models.PointField(blank=True, null=True, geography=True)

    NESHAN_KEY = 'web.ddd2ba2863e544f1b17fed49880c930e'

    def reverse_geocode_neshan(self, lat, lon):
        cache_key = f"neshan_rev_{lat}_{lon}"
        cached = cache.get(cache_key)
        if cached: return cached

        url = f"https://api.neshan.org/v5/reverse?lat={lat}&lng={lon}"
        headers = {"Api-Key": self.NESHAN_KEY}
        
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                cache.set(cache_key, data, 60 * 60 * 24) # کش برای یک روز
                return data
        except Exception: pass
        return {}

    def clean(self):
        # اگر نقطه انتخاب شده ولی فیلدها خالی هستند
        if self.point and not self.city:
            lat, lon = self.point.y, self.point.x
            data = self.reverse_geocode_neshan(lat, lon)
            
            if data:
                self.city = data.get("city") or data.get("state")
                self.district = data.get("district")
                self.full_address = data.get("formatted_address")
                # کشور را معمولاً ثابت نگه می‌داریم مگر پروژه بین‌المللی باشد

    def save(self, *args, **kwargs):
        self.full_clean() # اجرای متد clean قبل از ذخیره
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.city} - {self.district or ''}"