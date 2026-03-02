"""URL routing for core views (auth, dashboard, settings, reports)."""
from django.urls import path
from django.views.generic import RedirectView
from django.urls import reverse_lazy
from . import views_html
from . import api_filters
from . import api_bulk_operations
from . import data_import
from . import analytics_dashboard

app_name = 'core'

urlpatterns = [
    # ━━━ Root URL - Redirect to dashboard ━━━
    path('', RedirectView.as_view(url=reverse_lazy('core:dashboard'), permanent=False), name='home'),
    
    # ━━━ Authentication ━━━
    path('auth/login/', views_html.login_view, name='login'),
    path('auth/register/', views_html.register_view, name='register'),
    path('auth/password-reset/', views_html.password_reset_view, name='password_reset'),
    path('auth/password-reset/<uidb64>/<token>/', views_html.password_reset_confirm_view, name='password_reset_confirm'),
    path('auth/logout-confirm/', views_html.logout_confirm_view, name='logout_confirm'),
    path('auth/profile/', views_html.profile_view, name='profile'),
    path('auth/settings/', views_html.settings_view, name='settings'),
    
    # ━━━ Dashboard ━━━
    path('dashboard/', views_html.dashboard_view, name='dashboard'),
    path('analytics/', views_html.analytics_dashboard_view, name='analytics-dashboard'),
    
    # ━━━ Reports ━━━
    path('reports/invoices/', views_html.invoices_report_view, name='reports-invoices'),
    path('reports/invoices/export-csv/', views_html.export_invoices_csv_view, name='export-invoices-csv'),
    path('reports/invoices/export-pdf/', views_html.invoices_report_pdf_view, name='invoices-report-pdf'),
    path('reports/payments/', views_html.payments_report_view, name='reports-payments'),
    path('reports/payments/export-csv/', views_html.export_payments_csv_view, name='export-payments-csv'),
    path('reports/payments/export-pdf/', views_html.payments_report_pdf_view, name='payments-report-pdf'),
    path('reports/vat/', views_html.vat_report_view, name='reports-vat'),
    path('reports/vat/export-pdf/', views_html.vat_report_pdf_view, name='vat-report-pdf'),
    path('reports/aging/', views_html.client_aging_view, name='reports-aging'),
    path('reports/aging/export-pdf/', views_html.client_aging_pdf_view, name='aging-report-pdf'),
    path('reports/outstanding/', views_html.outstanding_invoices_view, name='reports-outstanding'),
    path('reports/outstanding/export-pdf/', views_html.outstanding_invoices_pdf_view, name='outstanding-report-pdf'),
    path('reports/product-sales/', views_html.product_sales_view, name='reports-product-sales'),
    path('reports/product-sales/export-pdf/', views_html.product_sales_pdf_view, name='sales-report-pdf'),
    path('reports/monthly-summary/', views_html.monthly_summary_view, name='reports-monthly-summary'),
    path('reports/monthly-summary/export-pdf/', views_html.monthly_summary_pdf_view, name='monthly-report-pdf'),
    path('reports/tax/', views_html.tax_report_view, name='reports-tax'),
    path('reports/tax/export-pdf/', views_html.tax_report_pdf_view, name='tax-report-pdf'),
    
    # ━━━ Quotation Reports ━━━
    path('reports/quotations/', views_html.quotations_report_view, name='reports-quotations'),
    path('reports/quotations/export-pdf/', views_html.quotations_report_pdf_view, name='quotations-report-pdf'),
    path('reports/quotations/pipeline/', views_html.quotation_pipeline_view, name='reports-quotation-pipeline'),
    path('reports/quotations/pipeline/export-pdf/', views_html.quotation_pipeline_pdf_view, name='quotation-pipeline-report-pdf'),
    path('reports/quotations/performance/', views_html.quotation_performance_view, name='reports-quotation-performance'),
    path('reports/quotations/performance/export-pdf/', views_html.quotation_performance_pdf_view, name='quotation-performance-report-pdf'),
    
    # ━━━ Settings ━━━
    path('settings/general/', views_html.settings_general_view, name='settings-general'),
    path('settings/company/', views_html.settings_company_view, name='settings-company'),
    path('settings/taxes/', views_html.settings_tax_view, name='settings-tax'),
    path('settings/invoice/', views_html.settings_invoice_view, name='settings-invoice'),
    path('settings/currency/', views_html.settings_currency_view, name='settings-currency'),
    path('settings/email/', views_html.settings_email_view, name='settings-email'),
    path('settings/email/test/', views_html.test_email_view, name='test-email'),
    
    # ━━━ User Account Settings ━━━
    path('settings/account/', views_html.settings_view, name='settings'),
    path('settings/account/update-profile/', views_html.update_profile, name='update_profile'),
    path('settings/account/change-password/', views_html.change_password, name='change_password'),
    path('settings/account/setup-2fa/', views_html.setup_2fa, name='setup_2fa'),
    path('settings/account/logout-other-sessions/', views_html.logout_all_other, name='logout_all_other'),
    path('settings/account/update-preferences/', views_html.update_preferences, name='update_preferences'),
    path('settings/account/update-notifications/', views_html.update_notifications, name='update_notifications'),
    path('settings/account/update-reminders/', views_html.update_reminders, name='update_reminders'),
    path('settings/account/create-api-key/', views_html.create_api_key, name='create_api_key'),
    path('settings/account/export-data/', views_html.export_data, name='export_data'),
    path('settings/account/delete/', views_html.delete_account_confirm, name='delete_account_confirm'),
    
    # ━━━ Admin Management ━━━
    path('system/users/', views_html.users_management_view, name='users-management'),
    path('system/users/create-edit/', views_html.users_create_edit_view, name='users-create-edit'),
    path('system/users/create-edit/<int:pk>/', views_html.users_create_edit_view, name='users-edit'),
    path('system/roles/', views_html.roles_management_view, name='roles-management'),
    path('system/permissions/', views_html.permission_management_view, name='permission-management'),
    path('system/role/<int:role_id>/permissions/', views_html.role_permissions_editor_view, name='role-permissions-editor'),
    path('system/permissions/matrix/', views_html.permission_matrix_view, name='permission-matrix'),
    path('system/audit-log/', views_html.audit_log_view, name='audit-log'),
    path('system/system-status/', views_html.system_status_view, name='system-status'),
    path('system/system-status/report/', views_html.system_status_report_view, name='system-status-report'),
    path('system/system-status/report/pdf/', views_html.system_status_report_pdf_view, name='system-status-report-pdf'),
    path('system/backup-restore/', views_html.backup_restore_view, name='backup-restore'),
    
    # ━━━ Help & Support ━━━
    path('help/', views_html.help_center_view, name='help-center'),
    path('help/faq/', views_html.faq_view, name='faq'),
    path('help/articles/', views_html.help_articles_view, name='help-articles'),
    path('help/articles/<slug:slug>/', views_html.help_article_detail_view, name='help-article-detail'),
    path('help/support/', views_html.support_form_view, name='support-form'),
    path('help/support/tickets/', views_html.support_tickets_view, name='support-tickets'),
    path('help/support/tickets/<str:ticket_number>/', views_html.support_ticket_detail_view, name='support-ticket-detail'),
    
    # ━━━ System Admin API Endpoints ━━━
    path('api/system/permissions/', views_html.get_permissions_api, name='system-permissions-api'),
    path('api/system/roles/<int:role_id>/permissions/', views_html.get_role_permissions_api, name='system-role-permissions-api'),
    path('api/system/roles/<int:role_id>/update-permissions/', views_html.update_role_permissions_api, name='system-update-permissions-api'),
    path('api/system/users/<int:user_id>/delete/', views_html.delete_user_api, name='system-delete-user-api'),
    
    # ━━━ Advanced Search & Filtering API ━━━
    path('api/filters/', api_filters.filter_api, name='filter-api'),
    path('api/filters/<int:filter_id>/', api_filters.filter_detail_api, name='filter-detail-api'),
    path('api/filters/options/', api_filters.filter_options_api, name='filter-options-api'),
    path('api/search/suggestions/', api_filters.search_suggestions_api, name='search-suggestions-api'),
    
    # ━━━ Bulk Operations API ━━━
    path('api/bulk/status-update/', api_bulk_operations.bulk_status_update, name='bulk-status-update'),
    path('api/bulk/send-email/', api_bulk_operations.bulk_send_email, name='bulk-send-email'),
    path('api/bulk/delete/', api_bulk_operations.bulk_delete, name='bulk-delete'),
    path('api/bulk/options/', api_bulk_operations.get_bulk_action_options, name='bulk-options'),
    
    # ━━━ Data Import API ━━━
    path('api/import/data/', data_import.import_data, name='import-data'),
    path('api/import/template/', data_import.get_import_template, name='import-template'),
    path('api/import/history/', data_import.get_import_history, name='import-history'),
    
    # ━━━ Analytics Dashboard API ━━━
    path('api/dashboard/', analytics_dashboard.get_dashboard_data, name='dashboard-data'),
    path('api/metrics/financial/', analytics_dashboard.get_financial_metrics, name='financial-metrics'),
    path('api/chart/timeline/', analytics_dashboard.get_timeline_chart, name='timeline-data'),
    path('api/report/aging/', analytics_dashboard.get_aging_report, name='aging-report'),
    path('api/metrics/payment-methods/', analytics_dashboard.get_payment_method_breakdown, name='payment-methods'),
    
    # ━━━ Analytics API (Dashboard Widget Endpoints) ━━━
    path('api/analytics/summary/', analytics_dashboard.get_financial_metrics, name='analytics-summary'),
    path('api/analytics/timeline/', analytics_dashboard.get_timeline_chart, name='analytics-timeline'),
    path('api/analytics/aging/', analytics_dashboard.get_aging_report, name='analytics-aging'),
    path('api/analytics/top-clients/', analytics_dashboard.get_top_clients, name='analytics-top-clients'),
    path('api/analytics/payment-methods/', analytics_dashboard.get_payment_method_breakdown, name='analytics-payment-methods'),
]
