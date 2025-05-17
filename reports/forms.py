from django import forms
from .models import Dashboard, Widget
from .constants import DATA_SOURCE_CONFIG
import json

class DashboardForm(forms.ModelForm):
    class Meta:
        model = Dashboard
        fields = ('name', 'description', 'is_shared')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_shared': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class WidgetForm(forms.ModelForm):
    DATA_SOURCE_CHOICES = [
        (key, config['description']) for key, config in DATA_SOURCE_CONFIG.items()
    ]
    
    data_source = forms.ChoiceField(choices=DATA_SOURCE_CHOICES, widget=forms.Select(attrs={
        'class': 'form-select'
    }))
    
    config = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
    
    class Meta:
        model = Widget
        fields = ('title', 'widget_type', 'data_source', 'width', 'height', 'config', 'refresh_interval')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'widget_type': forms.Select(attrs={'class': 'form-select'}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'min': 100}),
            'refresh_interval': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
    
    def clean_config(self):
        config = self.cleaned_data.get('config')
        if not config:
            return {}
        try:
            return json.loads(config)
        except json.JSONDecodeError:
            raise forms.ValidationError("Invalid JSON configuration")
    
    def clean(self):
        cleaned_data = super().clean()
        widget_type = cleaned_data.get('widget_type')
        data_source = cleaned_data.get('data_source')
        
        if widget_type and data_source:
            compatible_widgets = DATA_SOURCE_CONFIG.get(data_source, {}).get('compatible_widgets', [])
            if widget_type not in compatible_widgets:
                raise forms.ValidationError(f"{widget_type} is not compatible with {data_source}")
        
        return cleaned_data