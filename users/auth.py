from django.utils.timezone import now
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from .serializers import CustomTokenObtainPairSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.exceptions import AuthenticationFailed
from users.models import User
from django.shortcuts import get_object_or_404

class CustomTokenObtainPairView(TokenObtainPairView):
    """Login to user account and return access and refresh tokens"""
    serializer_class = CustomTokenObtainPairSerializer

    @swagger_auto_schema(
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'access_token': openapi.Schema(type=openapi.TYPE_STRING, description="JWT access token"),
                    'refresh_token': openapi.Schema(type=openapi.TYPE_STRING, description="JWT refresh token"),
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

            return Response({
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class CustomTokenRefreshView(TokenRefreshView):
    """Generate new access token using refresh token"""

    @swagger_auto_schema(
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

            if user.role == "employer":
                new_refresh_token["company_name"] = user.company_name
                new_refresh_token["industry"] = user.industry

            return Response({
                "access_token": str(new_refresh_token.access_token),
                "refresh_token": str(new_refresh_token),
            }, status=status.HTTP_200_OK)

        except TokenError:
            return Response({"error": "Invalid or expired refresh token"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
