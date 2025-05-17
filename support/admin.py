from django.contrib import admin
from .models import TicketCategory, SupportTicket, TicketComment, TicketStatusUpdate

class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 0
    readonly_fields = ('author', 'created_at')

class TicketStatusUpdateInline(admin.TabularInline):
    model = TicketStatusUpdate
    extra = 0
    readonly_fields = ('changed_by', 'changed_at')

class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'subject', 'client', 'priority', 'status', 'assigned_to', 'created_at')
    list_filter = ('status', 'priority', 'category', 'assigned_to')
    search_fields = ('ticket_number', 'subject', 'client__company')
    readonly_fields = ('ticket_number', 'created_by', 'resolved_at')
    date_hierarchy = 'created_at'
    inlines = [TicketCommentInline, TicketStatusUpdateInline]
    
    fieldsets = (
        (None, {
            'fields': ('ticket_number', 'client', 'subject', 'description')
        }),
        ('Classification', {
            'fields': ('category', 'priority', 'status')
        }),
        ('Assignment', {
            'fields': ('assigned_to',)
        }),
        ('Resolution', {
            'fields': ('resolved_at',)
        }),
        ('Metadata', {
            'fields': ('created_by',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, TicketComment) and not instance.pk:
                instance.author = request.user
            if isinstance(instance, TicketStatusUpdate) and not instance.pk:
                instance.changed_by = request.user
            instance.save()
        formset.save_m2m()

admin.site.register(TicketCategory)
admin.site.register(SupportTicket, SupportTicketAdmin)
admin.site.register(TicketComment)
admin.site.register(TicketStatusUpdate)