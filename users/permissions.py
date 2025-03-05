from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerBasedOnRole(BasePermission):
    """
    Custom permission:
    - Admins can read & modify everything.
    - Users can only read all but only modify their own objects.
    - Employers can read all objects but modify only their own.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True

        # Users and employers can only modify their own data
        return getattr(request.user, "role", None) in ["user", "employer"]

    def has_object_permission(self, request, view, obj):
        """
        Grant access based on role:
        - Admins can access & modify all objects.
        - Users can access all but modify only their own records.
        - Employers can read all objects but modify only their own.
        """
        if request.user.is_superuser:
            return True

        if request.user.role in ["user", "employer"]:
            return hasattr(obj, "user") and obj.user == request.user

        return False


class IsOnlyAdmin(BasePermission):
    """Allows access only to superadmins or users with the 'admin' role."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_superuser or getattr(request.user, "role", None) == "admin"
        )
    
    def has_object_permission(self, request, view, obj):
        return request.user.is_superuser or getattr(request.user, "role", None) == "admin"
    

class CanCreateUserOrEmployer(BasePermission):
    """
    Allows anyone to create a 'user' or 'employer' account but restricts 'admin' account creation to existing admins.
    """
    def has_permission(self, request, view):
        if request.method == "POST":
            role = request.data.get("role", "").lower()

            if role in ["user", "employer"]:
                return True

            if role == "admin":
                return request.user.is_authenticated and request.user.is_superuser

        return True
