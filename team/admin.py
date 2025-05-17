from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from .models import TeamMember, Role

admin.site.unregister(Group)

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role_display', 'is_active', 'is_staff', 'created_by')
    list_filter = ('role', 'is_active', 'is_staff', 'custom_role')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'profile_picture', 'bio')
        }),
        ('Professional Info', {
            'fields': ('department', 'job_title', 'created_by')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'role', 'custom_role', 'user_permissions'),
        }),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    filter_horizontal = ('user_permissions',)

class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'permissions_count')
    filter_horizontal = ('permissions',)
    search_fields = ('name', 'description')

    def permissions_count(self, obj):
        return obj.permissions.count()
    permissions_count.short_description = 'Permissions'

admin.site.register(TeamMember, CustomUserAdmin)
admin.site.register(Role, RoleAdmin)