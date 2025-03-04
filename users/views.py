from .models import User, UserProfile, EmployerProfile
from .serializers import UserSerializer, UserProfileSerializer, EmployerProfileSerializer
from rest_framework import generics, viewsets, filters
from users.permissions import IsOwnerBasedOnRole, IsOnlyAdmin
from jobs.pagination import CustomPagination
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

class UserViewSet(viewsets.ModelViewSet):
    """API for retrieving and managing users, with categorized users endpoint."""
    queryset = User.objects.all().order_by("-createdAt")
    serializer_class = UserSerializer
    permission_classes = [IsOnlyAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ["email", "role", "company_name", "username", "first_name", "last_name"]
    pagination_class = CustomPagination

    @swagger_auto_schema(
        operation_summary="Admin API for Listing all Users",
        operation_description=(
        "Fetch a paginated list of users. Only admin have priviledge."
        "- Admin can search users by their first_name, last_name, role, email, company_name. \n\n"
        "- Admin can set size of data retrieved using page_size and can navigate to any page using page. \n\n"
        "- Only authorized admin can access this endpoint."
    ),
        responses={200: UserSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Admin API for Creating new user",
        operation_description="API for admin to create new user. Only admin have priviledge",
        request_body=UserSerializer,
        responses={
             201: openapi.Response("Account created successfully.", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={"message": openapi.Schema(type=openapi.TYPE_STRING)})),
            400: openapi.Response("Validation error (e.g., already created).", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={"error": openapi.Schema(type=openapi.TYPE_STRING)})),
        
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Admin API for Retrieving a user",
        operation_description="Get detailed information about a specific user. Only admin have priviledge",
        responses={200: UserSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Admin API for Updating a user",
        operation_description="Modify an existing user. Only admins have privilege.",
        request_body=UserSerializer,
        responses={200: UserSerializer, 400: "Bad Request"}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Admin API FOR Partially Updat a inguser",
        operation_description="Modify certain fields of an existing user. Only admins have privilege.",
        request_body=UserSerializer,
        responses={200: UserSerializer, 400: "Bad Request"}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Admin API for Deleting a user",
        operation_description="Remove a user from the system. Only admins have privilege.",
        responses={204: "No Content", 403: "Forbidden"}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

class UserProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a user's full profile.

    - `GET`: Retrieve a user profile.
    - `PUT`: Update a user profile.
    - `PATCH`: Partially update a user profile.
    - `DELETE`: Delete a user profile.
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    lookup_field = "user"
    permission_classes = [IsOwnerBasedOnRole]

    @swagger_auto_schema(
        operation_summary="Retrieve a user's profile",
        operation_description="Retrieve a user's profile by user ID.",
        responses={200: UserProfileSerializer(), 404: "User profile not found"},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update a user's profile",
        operation_description=(
            "Update an user's profile by user ID.\n\n"
            "- This is the endpoint that user can use to modify it's own account.\n\n"
            "- **N.B**: fields like password, groups, user_permissions, is_staff, is_superuser and role cannot be modified by the user, although when passed it will still give response 201.\n\n"
            "- Modifying fields like this will require user to reach admin.\n\n"
            "- Check documentation for endpoint to change password for user."
        ),
        request_body=UserProfileSerializer,
        responses={200: UserProfileSerializer(), 400: "Invalid data", 401: "Unauthenticated", 403: "Not authorized", 404: "User profile not found", 500: "Server error"},
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update a user's profile partially",
        operation_description=(
            "Partially update an user's profile by user ID.\n\n"
            "- This is the endpoint that user can use to partially modify it's own details.\n\n"
            "- **N.B**: fields like password, groups, user_permissions, is_staff, is_superuser and role cannot be modified by the user, although when passed it will still give response 201.\n\n"
            "- Modifying fields like this will require user to reach admin.\n\n"
            "- Check documentation for endpoint to change password for user."
        ),
        request_body=UserProfileSerializer,
        responses={200: UserProfileSerializer(), 400: "Invalid data", 401: "Unauthenticated", 403: "Not authorized", 404: "User profile not found", 500: "Server error"},
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a user's profile",
        operation_description="Delete a user's profile.",
        responses={204: "No Content", 401: "Unauthenticated", 403: "Not authorized", 404: "User profile not found", 500: "Server error"},
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class EmployerProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an employer's full profile.

    - `GET`: Retrieve an employer profile.
    - `PUT`: Update an employer profile.
    - `PATCH`: Partially update an employer profile.
    - `DELETE`: Delete an employer profile.
    """
    queryset = EmployerProfile.objects.all()
    serializer_class = EmployerProfileSerializer
    lookup_field = "user"
    permission_classes = [IsOwnerBasedOnRole]

    @swagger_auto_schema(
        operation_summary="Retrieve an employer's profile",
        operation_description=(
            "Fetch an employer's profile by employer ID to view details of employer."
        ),
        responses={200: EmployerProfileSerializer(), 404: "Employer profile not found"},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update an employer's profile",
        operation_description=(
            "Update an employer's profile by employer ID.\n\n"
            "- This is the endpoint that employer can use to modify it's own account.\n\n"
            "- **N.B**: fields like password, groups, user_permissions, is_staff, is_superuser and role cannot be modified by the employer, although when passed it will still give response 201.\n\n"
            "- Modifying fields like this will require employer to reach admin.\n\n"
            "- Check documentation for endpoint to change password for employer."
        ),
        request_body=EmployerProfileSerializer,
        responses={200: EmployerProfileSerializer(), 400: "Invalid data", 401: "Unauthenticated", 403: "Not authorized", 404: "Employer profile not found", 500: "Server error"},
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update an employer's profile",
        operation_description=(
            "Partially update an employer's profile by employer ID.\n\n"
            "- This is the endpoint that employer can use to partially modify it's own details.\n\n"
            "- **N.B**: fields like password, groups, user_permissions, is_staff, is_superuser and role cannot be modified by the employer, although when passed it will still give response 201.\n\n"
            "- Modifying fields like this will require employer to reach admin.\n\n"
            "- Check documentation for endpoint to change password for employer."
        ),
        request_body=EmployerProfileSerializer,
        responses={200: EmployerProfileSerializer(), 400: "Invalid data", 401: "Unauthenticated", 403: "Not authorized", 404: "Employer profile not found", 500: "Server error"},
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete an employer's profile",
        operation_description="Delete an employer's profile.",
        responses={204: "No content",  401: "Unauthenticated", 403: "Not authorized", 404: "Employer profile not found", 500: "Server error"},
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

