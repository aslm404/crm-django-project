from django.contrib import admin
from chat.consumers import User
from .models import Client, ClientNote, ClientFile

class ClientNoteInline(admin.TabularInline):
    model = ClientNote
    extra = 0
    readonly_fields = ('created_by', 'created_at')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'created_by':
            kwargs['initial'] = request.user
            kwargs['queryset'] = User.objects.filter(id=request.user.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class ClientFileInline(admin.TabularInline):
    model = ClientFile
    extra = 0
    readonly_fields = ('uploaded_by', 'uploaded_at')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'uploaded_by':
            kwargs['initial'] = request.user
            kwargs['queryset'] = User.objects.filter(id=request.user.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class ClientAdmin(admin.ModelAdmin):
    list_display = ('company', 'user', 'website', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('company', 'user__username', 'vat_number')
    inlines = [ClientNoteInline, ClientFileInline]
    fieldsets = (
        (None, {
            'fields': ('user', 'company', 'logo')
        }),
        ('Contact Info', {
            'fields': ('address', 'website', 'phone')
        }),
        ('Financial Info', {
            'fields': ('vat_number', 'payment_terms', 'preferred_currency')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.user:
            obj.user = request.user
        super().save_model(request, obj, form, change)

admin.site.register(Client, ClientAdmin)