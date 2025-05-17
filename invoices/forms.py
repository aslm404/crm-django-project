from django import forms
from .models import Invoice, Payment, RecurringInvoice
from clients.models import Client
from projects.models import Project
from django.db.models import Q

class InvoiceItemForm(forms.Form):
    description = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Item description'
    }))
    quantity = forms.DecimalField(widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'placeholder': 'Qty',
        'min': 1,
        'step': 1
    }))
    unit_price = forms.DecimalField(widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'placeholder': 'Price',
        'min': 0,
        'step': 0.01
    }))

InvoiceItemFormSet = forms.formset_factory(InvoiceItemForm, extra=1, can_delete=True)

class InvoiceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields['client'].queryset = Client.objects.all() if user.is_staff else Client.objects.filter(user=user)
            self.fields['project'].queryset = Project.objects.all() if user.is_staff else Project.objects.filter(Q(team_members=user) | Q(created_by=user)).distinct()
    
    class Meta:
        model = Invoice
        fields = ('client', 'project', 'issue_date', 'due_date', 'currency', 
                 'tax_rate', 'discount', 'notes', 'terms', 'footer')
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'terms': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'footer': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ('amount', 'payment_method', 'transaction_id', 'payment_date', 'notes')
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class RecurringInvoiceForm(forms.ModelForm):
    class Meta:
        model = RecurringInvoice
        fields = ('base_invoice', 'recurrence', 'is_active')
        widgets = {
            'base_invoice': forms.Select(attrs={'class': 'form-select'}),
            'recurrence': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }