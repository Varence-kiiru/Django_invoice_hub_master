from django.urls import path, include
from .views_signup import (
    signup_view, login_view, logout_view, 
    company_setup_view, email_verification_view, 
    password_reset_view
)
from .views_billing import (
    billing_dashboard_view, plan_upgrade_view, 
    payment_method_view, invoice_history_view
)
from .webhooks import stripe_webhook

app_name = 'organizations'

urlpatterns = [
    # Authentication URLs
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('company-setup/', company_setup_view, name='company_setup'),
    path('verify-email/<str:token>/', email_verification_view, name='email_verification'),
    path('password-reset/', password_reset_view, name='password_reset'),
    
    # Billing URLs
    path('billing/', billing_dashboard_view, name='billing_dashboard'),
    path('billing/upgrade/', plan_upgrade_view, name='upgrade'),
    path('billing/payment-method/', payment_method_view, name='payment_method'),
    path('billing/invoices/', invoice_history_view, name='invoices'),
    
    # Stripe Webhook
    path('webhooks/stripe/', stripe_webhook, name='stripe-webhook'),
]
