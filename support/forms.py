from django import forms
from .models import SupportTicket, TicketComment, TicketCategory
from clients.models import Client
from team.models import TeamMember

class TicketForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and user.role == 'client':
            self.fields['client'].queryset = Client.objects.filter(user=user)
            self.fields['client'].initial = Client.objects.filter(user=user).first()
            self.fields['client'].disabled = True
        else:
            self.fields['client'].queryset = Client.objects.all()

        # Remove the category field if user is admin
        if user and user.role == 'admin':
            self.fields.pop('category', None)
        else:
            self.fields['category'].queryset = TicketCategory.objects.all()
            self.fields['category'].empty_label = "Select a category"
    
    class Meta:
        model = SupportTicket
        fields = ('subject', 'client', 'description', 'priority', 'category')
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

class TicketCommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ('content', 'attachments', 'is_internal')
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_internal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class TicketStatusForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter assigned_to based on user role
        if user and user.is_authenticated:
            if user.role == 'admin' and not user.is_superuser:
                # For admins, show only team members they created
                self.fields['assigned_to'].queryset = TeamMember.objects.filter(created_by=user)
            else:
                # For superusers or other roles (manager, staff), show all active team members
                self.fields['assigned_to'].queryset = TeamMember.objects.filter(is_active=True)
        else:
            # Fallback: show no team members if user is not authenticated
            self.fields['assigned_to'].queryset = TeamMember.objects.none()

    class Meta:
        model = SupportTicket
        fields = ('status', 'assigned_to')
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }

class TicketCategoryForm(forms.ModelForm):
    class Meta:
        model = TicketCategory
        fields = ('name', 'description')
        widgets = {
            'name': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }