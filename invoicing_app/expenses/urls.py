"""URL routing for expenses app - both HTML and API views."""

from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views_html
from .views import ExpenseViewSet, ExpenseCategoryViewSet, VendorViewSet

app_name = "expenses"

# API Router
router = DefaultRouter()
router.register(r"categories", ExpenseCategoryViewSet)
router.register(r"vendors", VendorViewSet)
router.register(r"expenses", ExpenseViewSet)

urlpatterns = [
    # ━━━ Expenses CRUD ━━━
    path("", views_html.expenses_list_view, name="list"),
    path("create/", views_html.expenses_create_view, name="create"),
    path("<int:pk>/", views_html.expenses_detail_view, name="detail"),
    path("<int:pk>/edit/", views_html.expenses_edit_view, name="edit"),
    path("<int:pk>/delete/", views_html.expenses_delete_view, name="delete"),
    # ━━━ Expenses Approval Workflow ━━━
    path("<int:pk>/submit/", views_html.expenses_submit_view, name="submit"),
    path("<int:pk>/approve/", views_html.expenses_approve_view, name="approve"),
    path("<int:pk>/reject/", views_html.expenses_reject_view, name="reject"),
    path("<int:pk>/mark-paid/", views_html.expenses_mark_paid_view, name="mark-paid"),
    # ━━━ Vendors Management ━━━
    path("vendors/", views_html.vendors_list_view, name="vendors-list"),
    path("vendors/create/", views_html.vendors_create_view, name="vendors-create"),
    path("vendors/<int:pk>/", views_html.vendors_detail_view, name="vendors-detail"),
    path("vendors/<int:pk>/edit/", views_html.vendors_edit_view, name="vendors-edit"),
    path(
        "vendors/<int:pk>/delete/",
        views_html.vendors_delete_view,
        name="vendors-delete",
    ),
    # ━━━ Categories ━━━
    path("categories/", views_html.categories_list_view, name="categories-list"),
    path(
        "categories/create/",
        views_html.categories_create_view,
        name="categories-create",
    ),
    path(
        "categories/<int:pk>/edit/",
        views_html.categories_edit_view,
        name="categories-edit",
    ),
    path(
        "categories/<int:pk>/delete/",
        views_html.categories_delete_view,
        name="categories-delete",
    ),
    # API endpoints are included via the main router in invoicing_app/urls.py
]

# The router is included in the main urls.py with: path('api/v1/', include((router.urls, 'api'), namespace='v1'))
