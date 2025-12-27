from django.urls import path
from rest_framework_simplejwt.views import TokenVerifyView

from .views import (
    SignupView,
    LoginView,
    RequestOTPView,
    VerifyOTPView,
    ResetPasswordView,
    UserProfileView,
    UserProfilePictureView,
    GoogleAuthView,
    SafeTokenRefreshView,
)


urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),

    path("otp/request/", RequestOTPView.as_view(), name="request-otp"),
    path("otp/verify/", VerifyOTPView.as_view(), name="verify-otp"),

    path("password/reset/", ResetPasswordView.as_view(), name="reset-password"),

    path("token/refresh/", SafeTokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),

    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("profile/picture/", UserProfilePictureView.as_view(), name="user-profile-picture"),
    path("login/google/", GoogleAuthView.as_view(), name="google-auth"),

]
