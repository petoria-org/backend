import random
from typing import Optional

from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, EmailVerification
from .serializers import LoginSerializer, SignupSerializer, VerifyOTPSerializer


# Create your views here.

def generate_otp_code() -> str:
    code = random.randint(1, 999999)
    return f"{code:06d}"

def invalidate_previous_otps(user: User):
    """
    Ensure only the newest OTP remains valid by marking older unused codes as used.
    """
    EmailVerification.objects.filter(user=user, is_used=False).update(is_used=True)


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request) -> Response:
        serializer = SignupSerializer(data=request.data)

        if serializer.is_valid():
            # user is created but not active
            user: User = serializer.save()
            # OTP
            code: str = generate_otp_code()
            invalidate_previous_otps(user)
            EmailVerification.objects.create(
                user=user,
                email=user.email,
                code=code,
                expires_at=timezone.now() + timezone.timedelta(minutes=5)
            )

            send_mail(
                subject="OTP Code",
                message=f"OTP code is: {code}",
                from_email="noreply@yourdomain.com",
                recipient_list=[user.email],
            )

            return Response(
                {"message": "User created. OTP sent to email."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RequestOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request) -> Response:
        """
        Request OTP code for login or forgot password
        """
        email: str = request.data.get('email')
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        user: Optional[User] = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "User with this email not found"}, status=status.HTTP_404_NOT_FOUND)

        code: str = generate_otp_code()
        invalidate_previous_otps(user)
        EmailVerification.objects.create(
            user=user,
            email=email,
            code=code,
            expires_at=timezone.now() + timezone.timedelta(minutes=5)
        )

        send_mail(
            subject="Your OTP Code",
            message=f"Your OTP code is: {code}",
            from_email="noreply@yourdomain.com",
            recipient_list=[email],
            fail_silently=False
        )

        return Response({"message": "OTP sent to email"}, status=status.HTTP_200_OK)



class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request) -> Response:
        serializer: VerifyOTPSerializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email: str = serializer.validated_data['email']
            code: str = serializer.validated_data['code']

            # Check OTP
            try:
                otp: EmailVerification = EmailVerification.objects.get(
                    user__email=email,
                    code=code,
                    is_used=False
                )
            except EmailVerification.DoesNotExist:
                return Response(
                    {"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

            if otp.expires_at < timezone.now():
                return Response({"error": "OTP expired."}, status=status.HTTP_400_BAD_REQUEST)

            # otp is valid -> activate the account
            otp.user.is_active = True
            otp.user.save()
            otp.is_used = True
            otp.save()

            return Response({"message": "OTP verified. User is now active."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request) -> Response:
        """
        Login user with username/email + password
        """
        serializer: LoginSerializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: User = serializer.validated_data['user']
        password: Optional[str] = serializer.validated_data.get('password')

        if not password:
            return Response({"error": "Password is required for login"}, status=status.HTTP_400_BAD_REQUEST)

        user_auth: Optional[User] = authenticate(username=user.username, password=password)
        if not user_auth:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user_auth)
        return Response(
            {
                "message": "Login successful",
                "username": user.username,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )




class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    def post(self, request) -> Response:
        """
        Reset password after verifying OTP
        """
        email: str = request.data.get('email')
        new_password: str = request.data.get('new_password')

        if not email or not new_password:
            return Response({"error": "Email and new password are required"}, status=status.HTTP_400_BAD_REQUEST)

        user: Optional[User] = User.objects.filter(email=email, is_active=True).first()
        if not user:
            return Response({"error": "User not found or not active"}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(new_password)
        user.save()

        return Response({"message": "Password has been reset successfully"}, status=status.HTTP_200_OK)
