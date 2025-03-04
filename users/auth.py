from django.utils.timezone import now
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from .serializers import CustomTokenObtainPairSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from users.permissions import CanCreateUserOrEmployer
from django.shortcuts import get_object_or_404
from .models import User, EmployerProfile
from .serializers import UserSerializer
from rest_framework import generics
from .tasks.email_tasks import send_welcome_email, send_employer_welcome_email

class CustomTokenObtainPairView(TokenObtainPairView):
    """Login to user account and return access and refresh tokens"""
    serializer_class = CustomTokenObtainPairSerializer

    @swagger_auto_schema(
        operation_summary="Sign in to access resources.",
        operation_description="API for all users to sign in into their account. It returns access and refresh token to access other protected endpoints.",
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'access_token': openapi.Schema(type=openapi.TYPE_STRING, description="JWT access token"),
                    'refresh_token': openapi.Schema(type=openapi.TYPE_STRING, description="JWT refresh token"),
                    'user': UserSerializer,
                }
            ),
            400: openapi.Response("Bad request"),
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.validated_data['user']
            user.last_login = now()
            user.save(update_fields=['last_login'])
            
            refresh = RefreshToken.for_user(user)
            refresh["email"] = user.email
            refresh["firstname"] = user.first_name
            refresh["lastname"] = user.last_name
            refresh["isStaff"] = user.is_staff
            refresh["isSuperAdmin"] = user.is_superuser
            refresh["isActive"] = user.is_active
            refresh["role"] = user.role
            refresh["phone"] = user.phone
            refresh["groups"] = list(user.groups.values_list("name", flat=True))
            refresh["permissions"] = list(user.user_permissions.values_list("codename", flat=True))
            if user.role == "employer":
                refresh["company_name"] = user.company_name
                refresh["industry"] = user.industry

            user_data = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "is_active": user.is_active,
            "role": user.role,
            "phone": user.phone,
            "groups": list(user.groups.values_list("name", flat=True)),
            "permissions": list(user.user_permissions.values_list("codename", flat=True))
        }

        if user.role == "employer":
            refresh["company_name"] = user.company_name
            refresh["industry"] = user.industry
            user_data["company_name"] = user.company_name
            user_data["industry"] = user.industry

        return Response(
            {
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "user": user_data,
            },
            status=status.HTTP_200_OK,
        )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class CustomTokenRefreshView(TokenRefreshView):
    """Generate new access token using refresh token"""

    @swagger_auto_schema(
        operation_summary="Get new access token using refresh token.",
        operation_description="API to keep user signed in by generating new access token after previous access token has expired.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "refresh_token": openapi.Schema(type=openapi.TYPE_STRING, description="Existing refresh token"),
            },
            required=["refresh_token"],
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "access_token": openapi.Schema(type=openapi.TYPE_STRING, description="New JWT access token"),
                    "refresh_token": openapi.Schema(type=openapi.TYPE_STRING, description="New refresh token"),
                    'user': UserSerializer,
                }
            ),
            400: openapi.Response("Bad request"),
        }
    )
    def post(self, request, *args, **kwargs):
        """Accepts a refresh token and returns a new access & refresh token"""
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)
            user_id = refresh["user_id"]

            user = get_object_or_404(User, id=user_id)

            new_refresh_token = RefreshToken.for_user(user)

            fields_to_preserve = [
                "email", "firstname", "lastname", "isStaff", "isSuperAdmin", 
                "isActive", "role", "groups", "permissions", "address", "phone",
                "token_type"
            ]

            for field in fields_to_preserve:
                if field in refresh:
                    new_refresh_token[field] = refresh[field]

            user_data = {
                "id": user.id,
                "email": user.email,
                "firstname": user.first_name,
                "lastname": user.last_name,
                "isStaff": user.is_staff,
                "isSuperAdmin": user.is_superuser,
                "isActive": user.is_active,
                "role": user.role,
                "phone": user.phone,
                "groups": list(user.groups.values_list("name", flat=True)),
                "permissions": list(user.user_permissions.values_list("codename", flat=True)),
            }

            if user.role == "employer":
                new_refresh_token["company_name"] = user.company_name
                new_refresh_token["industry"] = user.industry
                user_data["company_name"] = user.company_name
                user_data["industry"] = user.industry

            return Response({
                "access_token": str(new_refresh_token.access_token),
                "refresh_token": str(new_refresh_token),
                "user": user_data
            }, status=status.HTTP_200_OK)

        except TokenError:
            return Response({"error": "Invalid or expired refresh token"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UserCreateView(generics.CreateAPIView):
    """Create new user account"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [CanCreateUserOrEmployer]
    
    def perform_create(self, serializer):
        user = serializer.save()
        if user.role == 'admin':
            user.is_staff = True
            user.is_superuser = True
            user.save(update_fields=["is_staff", "is_superuser"])

        elif user.role == 'user':
            send_welcome_email.delay(user.email, user.first_name)

        elif user.role == 'employer':
            employer_profile = EmployerProfile.objects.filter(user=user).first()
            if employer_profile:
                send_employer_welcome_email.delay(user.email, user.company_name)
    
    @swagger_auto_schema(
        operation_summary="Sign up new account. (Public access signup)",
        operation_description="API endpoint for creating a new account. Based on role, either a User or Employer profile is created automatically.",
        request_body=UserSerializer,
        responses={201: "Account created successfully. A welcome email has been sent."},
    )
    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        return Response(
            {"message": "Account created successfully. A welcome email has been sent."},
            status=status.HTTP_201_CREATED,
        )