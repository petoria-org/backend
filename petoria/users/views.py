import random
from typing import Optional

from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.utils import timezone
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import EmailVerification
from .models import User
from .serializers import LoginSerializer, SignupSerializer, VerifyOTPSerializer
from .serializers import UserSerializer



class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        google_token = request.data.get("token")

        if not google_token:
            return Response({"error": "Token is required"}, status=400)

        try:
            # Validate token with Google
            GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
            info = id_token.verify_oauth2_token(
                google_token,
                google_requests.Request(),
                GOOGLE_CLIENT_ID
            )
        except Exception:
            return Response({"error": "Invalid Google token"}, status=400)

        google_id = info.get("sub")
        email = info.get("email")
        first_name = info.get("given_name", "")
        last_name = info.get("family_name", "")

        if not email:
            return Response({"error": "Google did not return email"}, status=400)

        # ----- SIGNUP + LOGIN -----
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "first_name": first_name,
                "last_name": last_name,
                "google_id": google_id,
                "is_active": True,
            }
        )

        # If old user but google_id not yet saved
        if not user.google_id:
            user.google_id = google_id
            user.save()

        # JWT
        refresh = RefreshToken.for_user(user)

        return Response({
            "status": "signup" if created else "login",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=200)


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

            try:
                send_mail(
                    subject="OTP Code",
                    message=f"OTP code is: {code}",
                    from_email="noreply@yourdomain.com",
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception:
                return Response(
                    {"error": "Failed to send OTP email. Please try again shortly."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
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

        try:
            send_mail(
                subject="Your OTP Code",
                message=f"Your OTP code is: {code}",
                from_email="noreply@yourdomain.com",
                recipient_list=[email],
                fail_silently=False
            )
        except Exception:
            return Response(
                {"error": "Failed to send OTP email. Please try again shortly."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({"message": "OTP sent to email"}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request) -> Response:
        serializer: VerifyOTPSerializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            purpose: str = serializer.validated_data.get('purpose')
            email: str = serializer.validated_data.get('email')
            code: str = serializer.validated_data.get('code')

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

            if purpose == "email":
                # otp is valid -> activate the account
                otp.user.is_active = True
                otp.user.save()
                otp.is_used = True
                otp.save()
                return Response({"message": "OTP verified. User is now active."}, status=status.HTTP_200_OK)

            elif purpose == "reset":
                return Response({"message": "OTP verified."}, status=status.HTTP_200_OK)

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
        if not user_auth.is_active:
            return Response({"error": "Account is not active. Please verify your email."},
                            status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user_auth)
        return Response(
            {
                "message": "Login successful",
                "username": user.username,
                "is_active": user.is_active,
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
        code: str = request.data.get('code')
        new_password: str = request.data.get('new_password')

        if not email or not code or not new_password:
            return Response({"error": "Email, OTP code, and new password are required"},
                            status=status.HTTP_400_BAD_REQUEST)

        user: Optional[User] = User.objects.filter(email=email, is_active=True).first()
        if not user:
            return Response({"error": "User not found or not active"}, status=status.HTTP_404_NOT_FOUND)

        try:
            otp: EmailVerification = EmailVerification.objects.get(
                user=user,
                code=code,
                is_used=False
            )
        except EmailVerification.DoesNotExist:
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        if otp.expires_at < timezone.now():
            return Response({"error": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        otp.is_used = True
        otp.save()

        return Response({"message": "Password has been reset successfully"}, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)


class UserProfilePictureView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded = request.FILES.get("profile_picture")
        if not uploaded:
            return Response({"error": "No profile picture provided."}, status=status.HTTP_400_BAD_REQUEST)

        content_type = (uploaded.content_type or "").lower()
        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        if content_type not in allowed_types:
            return Response({"error": "Unsupported file type."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        default_name = user._meta.get_field("profile_picture").get_default()
        if user.profile_picture and user.profile_picture.name != default_name:
            user.profile_picture.delete(save=False)

        user.profile_picture = uploaded
        user.save(update_fields=["profile_picture"])
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

    def delete(self, request):
        user = request.user
        default_name = user._meta.get_field("profile_picture").get_default()
        if user.profile_picture and user.profile_picture.name != default_name:
            user.profile_picture.delete(save=False)

        user.profile_picture = default_name
        user.save(update_fields=["profile_picture"])
        return Response(status=status.HTTP_204_NO_CONTENT)
