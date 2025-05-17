from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'invoices'

router = DefaultRouter()
router.register(r'api/invoices', views.InvoiceViewSet, basename='invoice')
router.register(r'api/payments', views.PaymentViewSet, basename='payment')
router.register(r'api/recurring-invoices', views.RecurringInvoiceViewSet, basename='recurring-invoice')

urlpatterns = [
    path('', views.InvoiceListView.as_view(), name='list'),
    path('create/', views.InvoiceCreateView.as_view(), name='create'),
    path('<int:pk>/', views.InvoiceDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.InvoiceUpdateView.as_view(), name='update'),
    path('<int:pk>/pdf/', views.InvoicePDFView.as_view(), name='pdf'),
    path('<int:pk>/send/', views.InvoiceSendView.as_view(), name='send'),
    path('<int:pk>/payment/', views.PaymentCreateView.as_view(), name='payment_create'),
    path('recurring/', views.RecurringInvoiceListView.as_view(), name='recurring_list'),
    path('recurring/create/', views.RecurringInvoiceCreateView.as_view(), name='recurring_create'),
    path('recurring/<int:pk>/edit/', views.RecurringInvoiceUpdateView.as_view(), name='recurring_update'),
    path('<int:invoice_id>/pay/stripe/', views.StripePaymentView.as_view(), name='stripe_payment'),
    path('<int:invoice_id>/pay/paypal/', views.PayPalPaymentView.as_view(), name='paypal_payment'),
    path('paypal/success/', views.PaymentSuccessView.as_view(), name='paypal_success'),
    path('paypal/cancel/', views.PaymentCancelView.as_view(), name='paypal_cancel'),
] + router.urls