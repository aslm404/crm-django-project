from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allows read-only access to everyone, but only allows writes for admins
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.role == 'admin'

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Allows access only to object owners or admins
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        owner = getattr(obj, 'created_by', None) or getattr(obj, 'user', None) or getattr(obj, 'owner', None)
        return owner == request.user

class IsClient(permissions.BasePermission):
    """
    Allows access only to clients
    """
    def has_permission(self, request, view):
        return request.user.role == 'client'

class HasCustomPermission(permissions.BasePermission):
    """
    Checks for specific model permissions
    """
    def __init__(self, *required_perms):
        self.required_perms = required_perms

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role == 'admin':
            return True
        return all(
            request.user.has_perm(perm)
            for perm in self.required_perms
        )

class IsSameUserOrAdmin(permissions.BasePermission):
    """
    Allows users to edit their own profile or admins
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        return obj == request.user

class RoleBasedPermissions(permissions.BasePermission):
    """
    Generic role-based permission checker
    """
    role_permissions = {
        'GET': ['admin', 'staff', 'client'],
        'POST': ['admin'],
        'PUT': ['admin'],
        'PATCH': ['admin'],
        'DELETE': ['admin'],
    }

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role == 'admin' or request.user.is_superuser:
            return True
        allowed_roles = self.role_permissions.get(request.method, [])
        if request.user.role in allowed_roles:
            return True
        if request.user.custom_role:
            required_perms = getattr(view, 'required_permissions', [])
            return any(request.user.has_perm(perm) for perm in required_perms)
        return False