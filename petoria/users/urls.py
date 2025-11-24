from django.urls import path

from .views import SignupView, LoginView, RequestOTPView, VerifyOTPView, ResetPasswordView

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("otp/request/", RequestOTPView.as_view(), name="request-otp"),
    path("otp/verify/", VerifyOTPView.as_view(), name="verify-otp"),
    path("password/reset/", ResetPasswordView.as_view(), name="reset-password"),
]
