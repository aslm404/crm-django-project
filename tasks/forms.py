from django import forms
from django.db.models import Q
from .models import Task, TimeEntry, RecurrencePattern, RecurringTask
from projects.models import Project
from team.models import TeamMember

class TaskForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['project'].queryset = Project.objects.filter(
                Q(team_members=user) | Q(created_by=user)
            ).distinct()
            
            if user.role == 'admin':
                # Only allow the logged-in admin as assignee
                self.fields['assignees'].queryset = TeamMember.objects.filter(id=user.id)
                self.fields['assignees'].initial = [user]
                self.fields['assignees'].disabled = True  # Optional: make it read-only in the form
            else:
                self.fields['assignees'].queryset = TeamMember.objects.filter(
                    role__in=['admin', 'client', 'staff']
                )

    class Meta:
        model = Task
        fields = ('title', 'project', 'description', 'status', 'priority', 'due_date', 'assignees', 'estimated_duration')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'assignees': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'estimated_duration': forms.TextInput(attrs={'class': 'form-control'}),
        }


class TimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        fields = ('task', 'start_time', 'end_time', 'description', 'invoice')
        widgets = {
            'task': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'invoice': forms.Select(attrs={'class': 'form-select'}),
        }

class RecurrencePatternForm(forms.ModelForm):
    weekdays = forms.MultipleChoiceField(
        choices=RecurrencePattern.WEEKDAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = RecurrencePattern
        fields = ('interval', 'frequency', 'weekdays', 'month_day', 'end_date', 'max_occurrences')
        widgets = {
            'interval': forms.Select(attrs={'class': 'form-select'}),
            'frequency': forms.NumberInput(attrs={'class': 'form-control'}),
            'month_day': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 31}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'max_occurrences': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

class RecurringTaskForm(forms.ModelForm):
    class Meta:
        model = RecurringTask
        fields = ('base_task', 'recurrence', 'is_active')
        widgets = {
            'base_task': forms.Select(attrs={'class': 'form-select'}),
            'recurrence': forms.Select(attrs={'class': 'form-select'}),
        }