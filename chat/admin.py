from django.contrib import admin
from .models import Conversation, Message

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'timestamp', 'read')
    ordering = ('-timestamp',)

class ConversationAdmin(admin.ModelAdmin):
    list_display = ('name', 'conversation_type', 'participants_count', 'client', 'updated_at')
    list_filter = ('conversation_type',)
    search_fields = ('name', 'participants__username', 'client__company')
    filter_horizontal = ('participants',)
    inlines = [MessageInline]
    
    def participants_count(self, obj):
        return obj.participants.count()
    participants_count.short_description = 'Participants'
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, Message) and not instance.sender:
                instance.sender = request.user
            instance.save()
        formset.save_m2m()

class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'content_preview', 'timestamp', 'read')
    list_filter = ('read', 'timestamp')
    search_fields = ('content', 'sender__username')
    
    def content_preview(self, obj):
        return obj.content[:50]
    content_preview.short_description = 'Content'

admin.site.register(Conversation, ConversationAdmin)
admin.site.register(Message, MessageAdmin)