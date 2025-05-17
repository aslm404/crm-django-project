from django.core.cache import cache
from django.contrib.auth.models import Permission
from .models import Role, TeamMember
from django.db.models import Q

def clear_permission_cache(user):
    """
    Clear cached permissions for a user
    """
    cache.delete(f'user_{user.id}_permissions')

def create_custom_role(name, permissions=None, description=""):
    """
    Create a new custom role with specified permissions
    """
    role, created = Role.objects.get_or_create(
        name=name,
        defaults={'description': description}
    )
    if permissions:
        role.permissions.set(permissions)
    return role

def get_users_with_permission(permission_codename, app_label):
    """
    Get all users who have a specific permission
    """
    permission = Permission.objects.get(codename=permission_codename, content_type__app_label=app_label)
    return TeamMember.objects.filter(
        Q(role='admin') |
        Q(custom_role__permissions=permission) |
        Q(user_permissions=permission)
    ).distinct()