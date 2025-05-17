from django import forms
from .models import Client, ClientNote, ClientFile
from team.models import TeamMember  # Import custom user model

class ClientForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Get user from view's get_form_kwargs
        super().__init__(*args, **kwargs)
        
        # For non-client users (admin/staff), show only client users in dropdown
        if user and user.is_authenticated and user.role in ['admin', 'staff']:
            self.fields['user'].queryset = TeamMember.objects.filter(role='client')
            self.fields['user'].widget.attrs.update({'class': 'form-select'})
        else:
            # For client users, hide user field and set to current user
            self.fields['user'].initial = user
            self.fields['user'].widget = forms.HiddenInput()

        # Ensure Bootstrap classes are applied to other fields
        for field_name, field in self.fields.items():
            if field_name != 'user' and field.widget.__class__.__name__ != 'FileInput':
                field.widget.attrs.update({'class': 'form-control'})
            elif field_name == 'logo':
                field.widget.attrs.update({'class': 'form-control'})
            # Update textarea rows for consistency
            if field_name in ['address', 'payment_terms']:
                field.widget.attrs.update({'rows': 3})

    class Meta:
        model = Client
        fields = ('user', 'company', 'address', 'website', 'vat_number', 
                  'payment_terms', 'preferred_currency', 'logo', 'phone')
        widgets = {
            'user': forms.Select(),
            'company': forms.TextInput(),
            'address': forms.Textarea(),
            'website': forms.URLInput(),
            'vat_number': forms.TextInput(),
            'payment_terms': forms.Textarea(),
            'preferred_currency': forms.Select(),
            'phone': forms.TextInput(),
            'logo': forms.FileInput(),
        }

class ClientNoteForm(forms.ModelForm):
    class Meta:
        model = ClientNote
        fields = ('content', 'is_public')
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ClientFileForm(forms.ModelForm):
    class Meta:
        model = ClientFile
        fields = ('file', 'description')
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }