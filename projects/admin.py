from django.contrib import admin
from .models import Project

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'status', 'start_date', 'deadline', 'progress_percentage', 'created_by')
    list_filter = ('status', 'client', 'created_by')
    search_fields = ('title', 'description', 'client__company')
    filter_horizontal = ('team_members',)
    readonly_fields = ('progress_percentage', 'created_at', 'updated_at')
    date_hierarchy = 'start_date'
    
    fieldsets = (
        (None, {
            'fields': ('title', 'client', 'description', 'status')
        }),
        ('Dates', {
            'fields': ('start_date', 'deadline')
        }),
        ('Financials', {
            'fields': ('budget',)
        }),
        ('Team', {
            'fields': ('team_members',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'progress_percentage', 'created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

admin.site.register(Project, ProjectAdmin)