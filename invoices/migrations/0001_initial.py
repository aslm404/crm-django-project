# Generated by Django 5.2 on 2025-05-05 05:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('clients', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_method', models.CharField(choices=[('cash', 'Cash'), ('check', 'Check'), ('bank_transfer', 'Bank Transfer'), ('credit_card', 'Credit Card'), ('paypal', 'PayPal'), ('stripe', 'Stripe')], max_length=20)),
                ('transaction_id', models.CharField(blank=True, max_length=100)),
                ('payment_date', models.DateField()),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='RecurringInvoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('next_run', models.DateField()),
                ('last_run', models.DateField(blank=True, null=True)),
                ('total_runs', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_number', models.CharField(max_length=50, unique=True)),
                ('issue_date', models.DateField()),
                ('due_date', models.DateField()),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('sent', 'Sent'), ('paid', 'Paid'), ('overdue', 'Overdue'), ('cancelled', 'Cancelled')], default='draft', max_length=20)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('tax_rate', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('discount', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('notes', models.TextField(blank=True)),
                ('terms', models.TextField(blank=True)),
                ('footer', models.TextField(blank=True)),
                ('items', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('total_amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoices', to='clients.client')),
            ],
        ),
    ]
