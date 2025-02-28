from rest_framework.decorators import action
from .models import User, UserProfile, EmployerProfile
from .serializers import UserSerializer, UserProfileSerializer, EmployerProfileSerializer
from rest_framework import generics, viewsets, filters
from rest_framework.permissions import AllowAny
from .tasks.email_tasks import send_welcome_email, send_employer_welcome_email
from rest_framework.response import Response
from rest_framework import status
from collections import defaultdict
from users.permissions import IsOwnerBasedOnRole, IsOnlyAdmin
from jobs.pagination import CustomPagination
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
class UserCreateView(generics.CreateAPIView):
    """Create new user account"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    
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

        return Response({"message": "Account created successfully. A welcome email has been sent."}, status=status.HTTP_201_CREATED)

class UserViewSet(viewsets.ModelViewSet):
    """API for retrieving and managing users, with categorized users endpoint."""
    
    queryset = User.objects.all().order_by("-createdAt")
    serializer_class = UserSerializer
    permission_classes = [IsOnlyAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ["email", "role", "company_name", "username"]
    pagination_class = CustomPagination


    @swagger_auto_schema(
        operation_summary="Get Users Categorized by Role",
        operation_description=(
            "This endpoint retrieves all users grouped by their roles, "
            "with pagination for each category."
        ),
        manual_parameters=[
            openapi.Parameter("page_size", openapi.IN_QUERY, description="Number of users per page (default: 10)", type=openapi.TYPE_INTEGER),
            openapi.Parameter("admin_page", openapi.IN_QUERY, description="Page number for 'admin' category", type=openapi.TYPE_INTEGER),
            openapi.Parameter("employer_page", openapi.IN_QUERY, description="Page number for 'employer' category", type=openapi.TYPE_INTEGER),
            openapi.Parameter("user_page", openapi.IN_QUERY, description="Page number for 'job_seeker or normal user' category", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response(
                description="Successfully retrieved categorized users",
                examples={
                    "application/json": {
                        "categories": {
                            "admin": {
                                "total_count": 25,
                                "users": [{"id": 1, "email": "admin@example.com", "role": "admin", "createdAt": "2024-02-26T12:00:00Z"}],
                                "pagination": {
                                    "next": "http://localhost:8000/api/users/categorized-users?page_size=10&admin_page=2",
                                    "previous": None,
                                },
                            },
                        }
                    }
                },
            ),
            400: openapi.Response("Invalid request parameters"),
            500: openapi.Response("Server error"),
        },
    )

    @action(detail=False, methods=["get"], url_path="categorized-users")
    def get_categorized_users(self, request):
        """Retrieve all users categorized by role with robust error handling and pagination."""
        try:
            users = User.objects.values("id", "email", "role", "createdAt").order_by("-createdAt")

            # Categorize users by role (handling None values)
            user_groups = defaultdict(list)
            for user in users:
                user_groups[user["role"] or "Other"].append(user)

            # Paginate each category
            paginated_categories = {}
            for role, user_list in user_groups.items():
                paginated_categories[role] = self._paginate_queryset(request, user_list, role)

            return Response({"categories": paginated_categories}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _paginate_queryset(self, request, user_list, category):
        """Paginate users efficiently with error handling."""
        page_size = int(request.GET.get("page_size", 10))
        page_number = request.GET.get(f"{category}_page", 1)

        paginator = Paginator(user_list, page_size)

        try:
            page = paginator.get_page(page_number)

            base_url = request.build_absolute_uri().split("?")[0]
            query_params = request.GET.dict()

            # Construct next/previous URLs
            query_params[f"{category}_page"] = page.next_page_number() if page.has_next() else None
            next_url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in query_params.items() if v is not None)}"

            query_params[f"{category}_page"] = page.previous_page_number() if page.has_previous() else None
            prev_url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in query_params.items() if v is not None)}"

            return {
                "total_count": paginator.count,
                "users": list(page),
                "pagination": {
                    "next": next_url if page.has_next() else None,
                    "previous": prev_url if page.has_previous() else None,
                },
            }

        except (EmptyPage, PageNotAnInteger):
            return {
                "total_count": paginator.count,
                "users": [],
                "pagination": {
                    "next": None,
                    "previous": None,
                },
                "error": "Invalid page number. Please check the available pages.",
            }
class UserProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve single user full profile for retrieval, update and deletion"""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    lookup_field = "user"
    permission_classes = [IsOwnerBasedOnRole]

class EmployerProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve single user full profile for retrieval, update and deletion"""
    queryset = EmployerProfile.objects.all()
    serializer_class = EmployerProfileSerializer
    lookup_field = "user"
    permission_classes = [IsOwnerBasedOnRole]
