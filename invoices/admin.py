from django.contrib import admin
from chat.consumers import User
from .models import Invoice, Payment, RecurringInvoice

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('recorded_by', 'created_at')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'recorded_by':
            kwargs['initial'] = request.user
            kwargs['queryset'] = User.objects.filter(id=request.user.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'client', 'issue_date', 'due_date', 'status', 'total_amount')
    list_filter = ('status', 'client', 'issue_date')
    search_fields = ('invoice_number', 'client__company')
    readonly_fields = ('invoice_number', 'subtotal', 'tax_amount', 'total_amount', 'created_by')
    date_hierarchy = 'issue_date'
    inlines = [PaymentInline]
    
    fieldsets = (
        (None, {
            'fields': ('invoice_number', 'client', 'project')
        }),
        ('Dates', {
            'fields': ('issue_date', 'due_date', 'status')
        }),
        ('Financials', {
            'fields': ('currency', 'tax_rate', 'discount', 'items')
        }),
        ('Calculations', {
            'fields': ('subtotal', 'tax_amount', 'total_amount')
        }),
        ('Content', {
            'fields': ('notes', 'terms', 'footer')
        }),
        ('Metadata', {
            'fields': ('created_by',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

class RecurringInvoiceAdmin(admin.ModelAdmin):
    list_display = ('base_invoice', 'recurrence', 'next_run', 'last_run', 'is_active')
    list_filter = ('is_active', 'recurrence__interval')
    search_fields = ('base_invoice__invoice_number',)
    readonly_fields = ('last_run', 'total_runs')

admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(RecurringInvoice, RecurringInvoiceAdmin)