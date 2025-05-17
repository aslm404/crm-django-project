from datetime import timezone
from django.views.generic import ListView, CreateView, DetailView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse, Http404
from django.template.loader import get_template
from django.contrib import messages
from xhtml2pdf import pisa
from .models import Invoice, Payment, RecurringInvoice
from .forms import InvoiceForm, PaymentForm, RecurringInvoiceForm, InvoiceItemFormSet
import stripe
from paypal.standard.forms import PayPalPaymentsForm
from django.conf import settings
from rest_framework import viewsets, permissions
from .serializers import InvoiceSerializer, PaymentSerializer, RecurringInvoiceSerializer
from clients.models import Client
import logging

logger = logging.getLogger(__name__)

class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'invoices/list.html'
    context_object_name = 'invoices'
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Invoice.objects.none()
        queryset = Invoice.objects.select_related('client', 'project', 'created_by')
        if user.is_superuser:
            return queryset
        elif user.role == 'admin':
            return queryset.filter(created_by=user)
        elif user.role == 'staff' and user.created_by:
            return queryset.filter(created_by=user.created_by)
        elif user.role == 'client':
            try:
                client = Client.objects.get(user=user)
                return queryset.filter(client=client)
            except Client.DoesNotExist:
                return queryset.none()
        return queryset.none()

class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoices/form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['item_formset'] = InvoiceItemFormSet(self.request.POST)
        else:
            context['item_formset'] = InvoiceItemFormSet()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']
        if item_formset.is_valid():
            form.instance.created_by = self.request.user
            form.instance.items = [
                {
                    'description': item['description'],
                    'quantity': item['quantity'],
                    'unit_price': item['unit_price']
                } for item in item_formset.cleaned_data if item
            ]
            return super().form_valid(form)
        return self.form_invalid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('invoices:detail', kwargs={'pk': self.object.pk})

class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'invoices/detail.html'
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Invoice.objects.none()
        queryset = Invoice.objects.select_related('client', 'project', 'created_by')
        if user.is_superuser:
            return queryset
        elif user.role == 'admin':
            return queryset.filter(created_by=user)
        elif user.role == 'staff' and user.created_by:
            return queryset.filter(created_by=user.created_by)
        elif user.role == 'client':
            try:
                client = Client.objects.get(user=user)
                return queryset.filter(client=client)
            except Client.DoesNotExist:
                return queryset.none()
        return queryset.none()
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        if user.is_superuser or \
           (user.role == 'admin' and obj.created_by == user) or \
           (user.role == 'staff' and user.created_by and obj.created_by == user.created_by) or \
           (user.role == 'client' and hasattr(user, 'client_profile') and obj.client == user.client_profile):
            return obj
        raise Http404("You do not have permission to view this invoice.")

class InvoiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoices/form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['item_formset'] = InvoiceItemFormSet(self.request.POST)
        else:
            context['item_formset'] = InvoiceItemFormSet(initial=self.object.items)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']
        if item_formset.is_valid():
            form.instance.items = [
                {
                    'description': item['description'],
                    'quantity': item['quantity'],
                    'unit_price': item['unit_price']
                } for item in item_formset.cleaned_data if item
            ]
            return super().form_valid(form)
        return self.form_invalid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Invoice.objects.none()
        if user.is_superuser:
            return Invoice.objects.all().select_related('client', 'project', 'created_by')
        elif user.role == 'admin':
            return Invoice.objects.filter(created_by=user).select_related('client', 'project', 'created_by')
        elif user.role == 'staff' and user.created_by:
            return Invoice.objects.filter(created_by=user.created_by).select_related('client', 'project', 'created_by')
        return Invoice.objects.none()
    
    def get_success_url(self):
        return reverse_lazy('invoices:detail', kwargs={'pk': self.object.pk})

class InvoicePDFView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'invoices/pdf.html'
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Invoice.objects.none()
        if user.is_superuser:
            return Invoice.objects.all().select_related('client', 'project', 'created_by')
        elif user.role == 'admin':
            return Invoice.objects.filter(created_by=user).select_related('client', 'project', 'created_by')
        elif user.role == 'staff' and user.created_by:
            return Invoice.objects.filter(created_by=user.created_by).select_related('client', 'project', 'created_by')
        elif user.role == 'client':
            try:
                client = Client.objects.get(user=user)
                return Invoice.objects.filter(client=client).select_related('client', 'project', 'created_by')
            except Client.DoesNotExist:
                return Invoice.objects.none()
        return Invoice.objects.none()
    
    def render_to_response(self, context, **response_kwargs):
        template = get_template(self.template_name)
        html = template.render(context)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{self.object.invoice_number}.pdf"'
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('PDF generation error')
        return response

class InvoiceSendView(LoginRequiredMixin, View):
    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        user = self.request.user
        if user.is_superuser or \
           (user.role == 'admin' and invoice.created_by == user) or \
           (user.role == 'staff' and user.created_by and invoice.created_by == user.created_by):
            invoice.status = 'sent'
            invoice.save()
            messages.success(request, 'Invoice has been sent to the client')
            return redirect('invoices:detail', pk=pk)
        raise Http404("You do not have permission to send this invoice.")

class PaymentCreateView(LoginRequiredMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'invoices/payment_form.html'
    
    def form_valid(self, form):
        form.instance.invoice_id = self.kwargs['pk']
        form.instance.recorded_by = self.request.user
        return super().form_valid(form)
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Invoice.objects.none()
        if user.is_superuser:
            return Invoice.objects.all().select_related('client', 'project', 'created_by')
        elif user.role == 'admin':
            return Invoice.objects.filter(created_by=user).select_related('client', 'project', 'created_by')
        elif user.role == 'staff' and user.created_by:
            return Invoice.objects.filter(created_by=user.created_by).select_related('client', 'project', 'created_by')
        return Invoice.objects.none()
    
    def get_success_url(self):
        return reverse_lazy('invoices:detail', kwargs={'pk': self.kwargs['pk']})

class RecurringInvoiceListView(LoginRequiredMixin, ListView):
    model = RecurringInvoice
    template_name = 'invoices/recurring_list.html'
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return RecurringInvoice.objects.none()
        if user.is_superuser:
            return RecurringInvoice.objects.all().select_related('base_invoice', 'base_invoice__created_by')
        elif user.role == 'admin':
            return RecurringInvoice.objects.filter(base_invoice__created_by=user).select_related('base_invoice', 'base_invoice__created_by')
        elif user.role == 'staff' and user.created_by:
            return RecurringInvoice.objects.filter(base_invoice__created_by=user.created_by).select_related('base_invoice', 'base_invoice__created_by')
        return RecurringInvoice.objects.none()

class RecurringInvoiceCreateView(LoginRequiredMixin, CreateView):
    model = RecurringInvoice
    form_class = RecurringInvoiceForm
    template_name = 'invoices/recurring_form.html'
    success_url = reverse_lazy('invoices:recurring_list')
    
    def form_valid(self, form):
        form.instance.base_invoice.created_by = self.request.user
        return super().form_valid(form)

class RecurringInvoiceUpdateView(LoginRequiredMixin, UpdateView):
    model = RecurringInvoice
    form_class = RecurringInvoiceForm
    template_name = 'invoices/recurring_form.html'
    success_url = reverse_lazy('invoices:recurring_list')
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return RecurringInvoice.objects.none()
        if user.is_superuser:
            return RecurringInvoice.objects.all().select_related('base_invoice', 'base_invoice__created_by')
        elif user.role == 'admin':
            return RecurringInvoice.objects.filter(base_invoice__created_by=user).select_related('base_invoice', 'base_invoice__created_by')
        elif user.role == 'staff' and user.created_by:
            return RecurringInvoice.objects.filter(base_invoice__created_by=user.created_by).select_related('base_invoice', 'base_invoice__created_by')
        return RecurringInvoice.objects.none()

class StripePaymentView(LoginRequiredMixin, View):
    def get(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, id=invoice_id)
        user = self.request.user
        if user.is_superuser or \
           (user.role == 'admin' and invoice.created_by == user) or \
           (user.role == 'staff' and user.created_by and invoice.created_by == user.created_by) or \
           (user.role == 'client' and hasattr(user, 'client_profile') and invoice.client == user.client_profile):
            stripe.api_key = settings.STRIPE_SECRET_KEY
            try:
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': invoice.currency.lower(),
                            'unit_amount': int(invoice.total * 100),
                            'product_data': {
                                'name': f'Invoice #{invoice.invoice_number}',
                            },
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    success_url=request.build_absolute_uri(reverse_lazy('invoices:detail', kwargs={'pk': invoice.id})),
                    cancel_url=request.build_absolute_uri(reverse_lazy('invoices:detail', kwargs={'pk': invoice.id})),
                )
                return redirect(checkout_session.url)
            except stripe.error.StripeError as e:
                logger.error(f"Stripe payment error for invoice {invoice.id}: {str(e)}")
                messages.error(request, f'Payment error: {str(e)}')
                return redirect('invoices:detail', pk=invoice.id)
        raise Http404("You do not have permission to process this payment.")

class PayPalPaymentView(LoginRequiredMixin, View):
    def get(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, id=invoice_id)
        user = self.request.user
        if user.is_superuser or \
           (user.role == 'admin' and invoice.created_by == user) or \
           (user.role == 'staff' and user.created_by and invoice.created_by == user.created_by) or \
           (user.role == 'client' and hasattr(user, 'client_profile') and invoice.client == user.client_profile):
            paypal_dict = {
                'business': settings.PAYPAL_RECEIVER_EMAIL,
                'amount': str(invoice.total),
                'item_name': f'Invoice #{invoice.invoice_number}',
                'invoice': str(invoice.id),
                'currency_code': invoice.currency,
                'notify_url': request.build_absolute_uri(reverse_lazy('paypal-ipn')),
                'return_url': request.build_absolute_uri(reverse_lazy('invoices:paypal_success')),
                'cancel_return': request.build_absolute_uri(reverse_lazy('invoices:paypal_cancel')),
            }
            form = PayPalPaymentsForm(initial=paypal_dict)
            return render(request, 'invoices/paypal_form.html', {'form': form, 'invoice': invoice})
        raise Http404("You do not have permission to process this payment.")

class PaymentSuccessView(LoginRequiredMixin, View):
    def get(self, request):
        invoice_id = request.GET.get('invoice')
        if invoice_id:
            invoice = get_object_or_404(Invoice, id=invoice_id)
            user = self.request.user
            if user.is_superuser or \
               (user.role == 'admin' and invoice.created_by == user) or \
               (user.role == 'staff' and user.created_by and invoice.created_by == user.created_by) or \
               (user.role == 'client' and hasattr(user, 'client_profile') and invoice.client == user.client_profile):
                Payment.objects.create(
                    invoice=invoice,
                    amount=invoice.total,
                    payment_method='paypal',
                    recorded_by=request.user,
                    payment_date=timezone.now().date()
                )
                invoice.status = 'paid'
                invoice.save()
                messages.success(request, 'Payment completed successfully.')
                return redirect('invoices:detail', pk=invoice.id)
            raise Http404("You do not have permission to process this payment.")
        messages.error(request, 'Invalid payment details.')
        return redirect('invoices:list')

class PaymentCancelView(LoginRequiredMixin, View):
    def get(self, request):
        invoice_id = request.GET.get('invoice')
        if invoice_id:
            messages.warning(request, 'Payment was cancelled.')
            return redirect('invoices:detail', pk=invoice_id)
        messages.error(request, 'Invalid payment details.')
        return redirect('invoices:list')

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Invoice.objects.select_related('client', 'project', 'created_by')
        if user.is_authenticated and not user.is_superuser:
            if user.role == 'admin':
                return queryset.filter(created_by=user)
            elif user.role == 'staff' and user.created_by:
                return queryset.filter(created_by=user.created_by)
            elif user.role == 'client':
                try:
                    client = Client.objects.get(user=user)
                    return queryset.filter(client=client)
                except Client.DoesNotExist:
                    return queryset.none()
        return queryset

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Payment.objects.select_related('invoice', 'recorded_by')
        if user.is_authenticated and not user.is_superuser:
            if user.role == 'admin':
                return queryset.filter(invoice__created_by=user)
            elif user.role == 'staff' and user.created_by:
                return queryset.filter(invoice__created_by=user.created_by)
            elif user.role == 'client':
                try:
                    client = Client.objects.get(user=user)
                    return queryset.filter(invoice__client=client)
                except Client.DoesNotExist:
                    return queryset.none()
        return queryset

class RecurringInvoiceViewSet(viewsets.ModelViewSet):
    queryset = RecurringInvoice.objects.all()
    serializer_class = RecurringInvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset().select_related('base_invoice', 'base_invoice__created_by')
        if user.is_authenticated and not user.is_superuser:
            if user.role == 'admin':
                return queryset.filter(base_invoice__created_by=user)
            elif user.role == 'staff' and user.created_by:
                return queryset.filter(base_invoice__created_by=user.created_by)
        return queryset