"""
URL routes for tax rate management.
"""
from django.urls import path
from . import views_html

app_name = 'taxes'

urlpatterns = [
    # Tax Rates - HTML views
    path('rates/', views_html.tax_rates_list, name='list'),
    path('rates/create/', views_html.tax_rate_create, name='create'),
    path('rates/<int:pk>/', views_html.tax_rate_detail, name='detail'),
    path('rates/<int:pk>/edit/', views_html.tax_rate_edit, name='edit'),
    path('rates/<int:pk>/delete/', views_html.tax_rate_delete, name='delete'),
    
    # VAT Rules
    path('vat-rules/', views_html.vat_rules_list, name='vat-rules-list'),
    path('vat-rules/create/', views_html.vat_rule_create, name='vat-rule-create'),
    path('vat-rules/<int:pk>/edit/', views_html.vat_rule_edit, name='vat-rule-edit'),
    path('vat-rules/<int:pk>/delete/', views_html.vat_rule_delete, name='vat-rule-delete'),
]
