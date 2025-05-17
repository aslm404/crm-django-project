from django.contrib import admin
from .models import Dashboard, Widget

class WidgetInline(admin.TabularInline):
    model = Widget
    extra = 0
    fields = ('title', 'widget_type', 'data_source', 'width', 'height', 'position')
    ordering = ('position',)

class DashboardAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'is_shared', 'created_at')
    list_filter = ('is_shared', 'created_by')
    search_fields = ('name', 'description')
    inlines = [WidgetInline]
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

admin.site.register(Dashboard, DashboardAdmin)