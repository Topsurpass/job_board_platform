from rest_framework import permissions

class ReadOnlyForAllUsersModifyByAdmin(permissions.BasePermission):
    """
    - Allow all users (authenticated or not) to view (GET).
    - Allow only admin and employer to modify (POST, PUT, PATCH, DELETE).
    - Allow only employer to modify their own objects.
    - Allow only admin to modify all objects.
    """

    def has_permission(self, request, view):
        # Allow GET requests for anyone (authenticated or not)
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.is_authenticated and (
            request.user.is_superuser or request.user.role == 'employer'
        )
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Admin can modify all objects
        if request.user.is_authenticated and request.user.is_superuser:
            return True

        # Employers can modify only their own objects
        if request.user.is_authenticated and hasattr(obj, 'posted_by') and obj.posted_by == request.user:
            return True
        
        if request.user.is_authenticated and hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True


class ReadCreateOnlyAdminModify(permissions.BasePermission):
    """
    - Users (applicants) can apply for jobs and list job applications they applied to.
    - Employers can only see applications submitted for jobs they posted.
    - Admins have full CRUD access.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        if request.method == "POST":
            return request.user.role == "user"

        return request.method in permissions.SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if request.method in permissions.SAFE_METHODS:
            if hasattr(obj, "job") and obj.job.posted_by == request.user:
                return True
            if hasattr(obj, "applicant") and obj.applicant == request.user:
                return True

        return False

"""
@swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "category",
                openapi.IN_QUERY,
                description="Category to filter jobs by (industry, location, or type)",
                type=openapi.TYPE_STRING,
                enum=["industry", "location", "type"],
                required=True,
            ),
            openapi.Parameter(
                "filter",
                openapi.IN_QUERY,
                description="Specific category value to filter (e.g., Lagos, Full-Time, Technology)",
                type=openapi.TYPE_STRING,
                required=False,
            ),
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Search for jobs by title, industry, location, or type",
                type=openapi.TYPE_STRING,
                required=False,
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Page number for pagination",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
            openapi.Parameter(
                "page_size",
                openapi.IN_QUERY,
                description="Number of jobs per page (default: 10)",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
        ],
        responses={
            200: openapi.Response(
                "Jobs categorized and paginated successfully",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "category_name": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "total_count": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "jobs": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                            "title": openapi.Schema(type=openapi.TYPE_STRING),
                                            "industry_name": openapi.Schema(type=openapi.TYPE_STRING),
                                            "location": openapi.Schema(type=openapi.TYPE_STRING),
                                            "type": openapi.Schema(type=openapi.TYPE_STRING),
                                            "wage": openapi.Schema(type=openapi.TYPE_NUMBER),
                                        },
                                    ),
                                ),
                                "pagination": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "next": openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                        "previous": openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    },
                                ),
                            },
                        )
                    },
                ),
            ),
            400: "Invalid request (e.g., missing required parameters)",
        },
    )

"""