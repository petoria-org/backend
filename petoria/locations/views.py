from django.shortcuts import render
from .models import Location


# Create your views here.
def locations_list(request):
    locations = Location.objects.all()
    return render(
        request,
        "path/to/locations/template/(.html)",
        {"locations": locations},
    )
