from django import forms
from .models import Project
from team.models import TeamMember

class ProjectForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        from clients.models import Client
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and user.is_authenticated and not user.is_superuser:
            self.fields['client'].queryset = Client.objects.filter()
            self.fields['team_members'].queryset = TeamMember.objects.filter(created_by=user)
        else:
            # For superusers, show all clients and active team members
            self.fields['client'].queryset = Client.objects.all()
            self.fields['team_members'].queryset = TeamMember.objects.filter(is_active=True)

    
    class Meta:
        model = Project
        fields = ('title', 'client', 'description', 'status', 'start_date', 
                 'deadline', 'budget', 'team_members')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control'}),
            'team_members': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }