from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class CustomAuthBackend(ModelBackend):
    """
    Custom authentication backend that allows login via either email or username,
    and supports role-based permission checks.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(Q(email=username) | Q(username=username))
        except UserModel.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user_permissions(self, user_obj, obj=None):
        if not user_obj.is_active or user_obj.is_anonymous:
            return set()
        return user_obj.get_all_permissions()

    def has_module_perms(self, user_obj, app_label):
        if user_obj.is_superuser:
            return True
        return any(
            perm.startswith(f'{app_label}.')
            for perm in self.get_user_permissions(user_obj)
        )