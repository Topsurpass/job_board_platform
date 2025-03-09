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
        
        if request.method in ["PUT", "PATCH"]:
            return request.user.role == "employer"

        return request.method in permissions.SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if request.method in permissions.SAFE_METHODS:
            if hasattr(obj, "job") and obj.job.posted_by == request.user:
                return True
            if hasattr(obj, "applicant") and obj.applicant == request.user:
                return True
        
        if request.method in ["PUT", "PATCH"]:
            if hasattr(obj, "job") and obj.job.posted_by == request.user:
                if "status" in request.data:
                    return True

        return False