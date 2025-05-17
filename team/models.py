from django.db import models
from django.contrib.auth.models import AbstractUser, Permission
from django.contrib.contenttypes.models import ContentType

class Role(models.Model):
    """Custom roles for users"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        limit_choices_to={'content_type__app_label__in': [
            'projects', 'tasks', 'invoices', 'clients', 'team', 'reports', 'chat', 'support'
        ]}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class TeamMember(AbstractUser):
    """Extended user model with HR Portal specific fields"""
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('client', 'Client'),
    )
    username = models.CharField(max_length=30, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    custom_role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL)
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True)
    bio = models.TextField(blank=True)
    department = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    is_online = models.BooleanField(default=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    email = models.EmailField(unique=True)
    created_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='created_users')

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def get_role_display(self):
        return self.custom_role.name if self.custom_role else dict(self.ROLE_CHOICES).get(self.role, self.role)

    def get_all_permissions(self):
        permissions = set()
        if self.is_superuser or self.role == 'admin':
            return set(Permission.objects.all())
        elif self.role == 'client':
            permissions.update(Permission.objects.filter(
                codename__in=['view_project', 'view_task', 'view_invoice']
            ))
        if self.custom_role:
            permissions.update(self.custom_role.permissions.all())
        return permissions