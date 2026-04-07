"""URL routing for payment management views."""

from django.urls import path
from . import views_html

app_name = "payments"

urlpatterns = [
    # ━━━ Payment CRUD ━━━
    path("", views_html.payments_list_view, name="list"),
    path("create/", views_html.payments_create_view, name="create"),
    path("<int:pk>/", views_html.payments_detail_view, name="detail"),
    path("<int:pk>/edit/", views_html.payments_edit_view, name="edit"),
    path("<int:pk>/delete/", views_html.payments_delete_view, name="delete"),
    # ━━━ Payment Management ━━━
    path(
        "reconciliation/", views_html.payment_reconciliation_view, name="reconciliation"
    ),
    path("<int:pk>/matching/", views_html.payment_matching_view, name="matching"),
    path("<int:pk>/receipt/", views_html.payment_receipt_view, name="receipt"),
    path(
        "<int:pk>/receipt/pdf/", views_html.payment_receipt_pdf_view, name="receipt_pdf"
    ),
    path(
        "<int:pk>/receipt/print/",
        views_html.payment_receipt_print_view,
        name="receipt_print",
    ),
    path(
        "<int:pk>/receipt/download/",
        views_html.payment_receipt_download_view,
        name="receipt_download",
    ),
    # ━━━ Payment Status Management ━━━
    path("<int:pk>/confirm/", views_html.confirm_payment_view, name="confirm"),
    path("<int:pk>/reverse/", views_html.reverse_payment_view, name="reverse"),
    # ━━━ Payment Methods ━━━
    path("methods/", views_html.payment_methods_list_view, name="methods-list"),
    path(
        "methods/create/", views_html.payment_method_create_view, name="method-create"
    ),
    path(
        "methods/<int:pk>/edit/",
        views_html.payment_method_edit_view,
        name="method-edit",
    ),
    path(
        "methods/<int:pk>/delete/",
        views_html.payment_method_delete_view,
        name="method-delete",
    ),
]
