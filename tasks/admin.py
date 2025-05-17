from django.contrib import admin
from .models import Task, TimeEntry, RecurringTask, RecurrencePattern

class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'priority', 'due_date', 'created_by', 'estimated_duration')
    list_filter = ('status', 'priority', 'project', 'created_by')
    search_fields = ('title', 'description', 'project__title')
    filter_horizontal = ('assignees',)
    date_hierarchy = 'due_date'
    
    fieldsets = (
        (None, {
            'fields': ('title', 'project', 'description')
        }),
        ('Status', {
            'fields': ('status', 'priority', 'estimated_duration')
        }),
        ('Dates', {
            'fields': ('due_date',)
        }),
        ('Assignees', {
            'fields': ('assignees',)
        }),
        ('Metadata', {
            'fields': ('created_by',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'start_time', 'duration', 'is_billed', 'invoice')
    list_filter = ('is_billed', 'user', 'task__project')
    search_fields = ('user__username', 'task__title', 'description')
    date_hierarchy = 'start_time'
    
    readonly_fields = ('duration',)

class RecurrencePatternAdmin(admin.ModelAdmin):
    list_display = ('interval', 'frequency', 'weekdays', 'month_day', 'end_date', 'max_occurrences')
    list_filter = ('interval',)

class RecurringTaskAdmin(admin.ModelAdmin):
    list_display = ('base_task', 'recurrence', 'next_run', 'last_run', 'is_active')
    list_filter = ('is_active', 'recurrence__interval')
    search_fields = ('base_task__title',)
    readonly_fields = ('last_run', 'total_runs')

admin.site.register(Task, TaskAdmin)
admin.site.register(TimeEntry, TimeEntryAdmin)
admin.site.register(RecurrencePattern, RecurrencePatternAdmin)
admin.site.register(RecurringTask, RecurringTaskAdmin)