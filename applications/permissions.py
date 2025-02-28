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
    - User can only create and list job applications
    - Employer can only see applications (applicants) for jobs they posted
    - Admin have all access to CRUD  
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
        
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        
        if request.method in permissions.SAFE_METHODS:
            return hasattr(obj, "job") and obj.job.posted_by == request.user
        
        if request.method in ["POST", "GET"]:
            return hasattr(obj, 'applicant') and obj.applicant == request.user
        return False
