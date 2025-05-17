from django import forms
from .models import Conversation, Message
from team.models import TeamMember
from clients.models import Client

class ConversationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and user.is_authenticated:
            if user.role == 'admin' and not user.is_superuser:
                # For admins, show only team members they created, excluding themselves
                self.fields['participants'].queryset = TeamMember.objects.filter(created_by=user).exclude(id=user.id)
            else:
                # For superusers or other roles, show all active team members, excluding themselves
                self.fields['participants'].queryset = TeamMember.objects.filter(is_active=True).exclude(id=user.id)
            self.fields['client'].queryset = Client.objects.filter()
        else:
            # Fallback: show no participants or clients if user is not authenticated
            self.fields['participants'].queryset = TeamMember.objects.none()
            self.fields['client'].queryset = Client.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        conversation_type = cleaned_data.get('conversation_type')
        client = cleaned_data.get('client')
        
        if conversation_type == 'client' and not client:
            raise forms.ValidationError("Client is required for client conversations.")
        if conversation_type == 'team' and client:
            raise forms.ValidationError("Client should not be set for team conversations.")
        
        return cleaned_data

    class Meta:
        model = Conversation
        fields = ('name', 'conversation_type', 'participants', 'client')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'conversation_type': forms.Select(attrs={'class': 'form-select'}),
            'participants': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('content', 'attachments')
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Type your message here...'
            }),
            'attachments': forms.FileInput(attrs={'class': 'form-control'}),
        }