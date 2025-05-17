from rest_framework import permissions

class ProjectPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == 'list':
            return True
        if view.action == 'create':
            return request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff)
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        is_owner = obj.created_by == request.user
        is_admin = request.user.is_superuser
        is_manager = request.user.is_staff and request.user in obj.team_members.all()
        
        if view.action in ['update', 'partial_update', 'team']:
            return is_owner or is_admin or is_manager
        if view.action == 'destroy':
            return is_owner or is_admin
        return False