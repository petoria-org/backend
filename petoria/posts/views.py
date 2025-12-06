from django.shortcuts import render
from .models import Lost_post, Found_post, Surrender_custody_pets


# Create your views here.
def lost_posts_list(request):
    lost_posts = Lost_post.objects.all()
    return render(request, "<placeholder path>", {"lost_posts": lost_posts})


def found_posts_list(request):
    found_posts = Found_post.objects.all()
    return render(request, "<placeholder path>", {"found_posts": found_posts})


def adaption_posts_list(request):
    adaption_posts = Surrender_custody_pets.objects.all()
    return render(request, "<placeholder path>", {"adaption_posts": adaption_posts})
