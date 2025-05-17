from rest_framework import serializers
from .models import Invoice, Payment, RecurringInvoice
from django.contrib.auth.models import User
from clients.models import Client
from projects.models import Project

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'company', 'user']

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'title', 'client']

class InvoiceSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    client = ClientSerializer(read_only=True)
    project = ProjectSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    tax_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True, source='total')
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'client', 'project', 'issue_date', 'due_date',
            'status', 'status_display', 'currency', 'tax_rate', 'discount', 'items',
            'subtotal', 'tax_amount', 'total', 'notes', 'terms', 'footer',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['invoice_number', 'created_by']

class PaymentSerializer(serializers.ModelSerializer):
    invoice = InvoiceSerializer(read_only=True)
    recorded_by = UserSerializer(read_only=True)
    method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'invoice', 'amount', 'payment_method', 'method_display',
            'transaction_id', 'payment_date', 'notes', 'recorded_by', 'created_at'
        ]
        read_only_fields = ['recorded_by']

class RecurringInvoiceSerializer(serializers.ModelSerializer):
    base_invoice = InvoiceSerializer(read_only=True)
    
    class Meta:
        model = RecurringInvoice
        fields = [
            'id', 'base_invoice', 'recurrence', 'next_run', 'last_run',
            'total_runs', 'is_active', 'created_at'
        ]