# locations/models.py
from typing import TypedDict, cast

import requests
from django.db import models
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator


class AddressDict(TypedDict, total=False):
    country: str
    city: str
    town: str
    village: str
    district: str
    suburb: str


class Location(models.Model):
    country: models.CharField = models.CharField(max_length=150, blank=True, null=True)
    city: models.CharField = models.CharField(max_length=150, blank=True, null=True)
    district: models.CharField = models.CharField(max_length=150, blank=True, null=True)

    # latitude = y, longitude = x
    latitude: models.FloatField = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
    )
    longitude: models.FloatField = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
    )

    def reverse_geocode(self, lat, lon):
        """
        Description : Convert coordinates → city/country using Nominatim
        @:param Param1: lat
        @:param Param2: lot
        @:return return1: city
        @:return return2: country
        """
        cache_key: str = f"rev_{lat}_{lon}"
        cached: dict[str, str] | None = cache.get(cache_key)

        if cached:
            return cached

        url: str = (
            "https://nominatim.openstreetmap.org/reverse"
            f"?lat={lat}&lon={lon}&format=json&zoom=10&addressdetails=1"
        )

        headers: dict[str, str] = {"User-Agent": "MahshidPetApp/1.0"}

        res: requests.Response = requests.get(url, headers=headers, timeout=5)

        if res.status_code != 200:
            return {}

        raw: dict[str, object] = res.json()  # -> Any (mypy: warning)
        data = cast(AddressDict, raw.get("address", {}))  # dict.get(key: str, default: T)
        cache.set(cache_key, data, 60 * 60)  # ۱ ساعت

        return data

    def forward_geocode(self, query):
        """
        Description: Convert text → coordinates using Nominatim
        @:return return1: latitude
        @:return return2: longitude
        """
        cache_key: str = f"fwd_{query}"
        cached: dict[str, str] = cache.get(cache_key)

        if cached:
            return cached

        url = (
            "https://nominatim.openstreetmap.org/search"
            f"?q={query}&format=json&limit=1"
        )

        headers: dict[str, str] = {"User-Agent": "MahshidPetApp/1.0"}

        res: requests.Response = requests.get(url, headers=headers, timeout=5)
        if res.status_code != 200:
            return None

        data: list[dict[str, object]] = res.json()
        cache.set(cache_key, data, 60 * 60)

        return data[0] if data else None

    def clean(self):
        """Validate + auto-fill fields intelligently"""
        has_lat = self.latitude is not None
        has_lon = self.longitude is not None
        if has_lat ^ has_lon:
            raise ValidationError("Both latitude and longitude must be provided together.")

        if has_lat and has_lon and (not self.country or not self.city):
            lat = self.latitude
            lon = self.longitude
            address = self.reverse_geocode(lat, lon)

            self.country = (
                    address.get("country") or self.country
            )
            self.city = (
                    address.get("city")
                    or address.get("town")
                    or address.get("village")
                    or self.city
            )
            self.district = (
                    address.get("district")
                    or address.get("suburb")
                    or self.district
            )

        if not has_lat and not has_lon and (self.city or self.country):
            query = ", ".join([p for p in [self.city, self.country] if p])
            result = self.forward_geocode(query)

            if result:
                self.latitude = float(result["lat"])
                self.longitude = float(result["lon"])

    def __str__(self):
        if self.latitude is not None and self.longitude is not None:
            return f"{self.city or ''}, {self.country or ''}".strip(" ,") or "Location"
        return self.city or self.country or "Unknown Location"
