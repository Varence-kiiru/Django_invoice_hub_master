"""URL routing for invoice management views."""

from django.urls import path
from . import views_html

app_name = "invoices"

urlpatterns = [
    # ━━━ Invoice CRUD ━━━
    path("", views_html.invoices_list_view, name="list"),
    path("create/", views_html.invoices_create_view, name="create"),
    path("<int:pk>/", views_html.invoices_detail_view, name="detail"),
    path("<int:pk>/edit/", views_html.invoices_edit_view, name="edit"),
    path("<int:pk>/delete/", views_html.invoices_delete_view, name="delete"),
    path("<int:pk>/view/", views_html.invoices_view_view, name="view"),
    # ━━━ Invoice Management ━━━
    path("<int:pk>/line-items/", views_html.invoice_line_items_view, name="line-items"),
    path(
        "<int:pk>/add-line-item/", views_html.add_line_item_view, name="add-line-item"
    ),
    path(
        "<int:pk>/edit-line-item/<int:line_item_id>/",
        views_html.edit_line_item_view,
        name="edit-line-item",
    ),
    path(
        "<int:pk>/remove-line-item/<int:line_item_id>/",
        views_html.remove_line_item_view,
        name="remove-line-item",
    ),
    path("<int:pk>/history/", views_html.invoice_history_view, name="history"),
    path("<int:pk>/pdf/", views_html.invoices_pdf_view, name="pdf"),
    path("<int:pk>/print/", views_html.invoices_print_view, name="print"),
    path("<int:pk>/display/", views_html.invoices_display_pdf_view, name="display"),
    path("<int:pk>/send/", views_html.invoices_send_view, name="send"),
    path("<int:pk>/cancel/", views_html.invoice_cancel_confirm_view, name="cancel"),
    path("<int:pk>/mark-paid/", views_html.invoice_mark_paid_view, name="mark-paid"),
    path("<int:pk>/clone/", views_html.invoice_clone_view, name="clone"),
    path("list/pdf/", views_html.invoices_view_pdf_view, name="list-pdf"),
    # ━━━ Invoice Reports ━━━
    path("outstanding/", views_html.invoices_outstanding_view, name="outstanding"),
]
