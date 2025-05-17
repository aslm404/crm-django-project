from rest_framework import permissions
from django.core.exceptions import PermissionDenied

class ClientPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user == request.user

class ClientAccessMixin:
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if self.request.user.is_staff or obj.user == self.request.user:
            return obj
        raise PermissionDenied