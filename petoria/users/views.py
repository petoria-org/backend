from django.shortcuts import render
from .models import User, EmailVerification


# Create your views here.
def users_list(request):
    users = User.objects.all()
    return render(request, "<placeholder path>", {"users": users})


def email_verifications_list(request):
    email_verifications = EmailVerification.objects.all()
    return render(
        request, "<placeholder path>", {"email_verifications": email_verifications}
    )
