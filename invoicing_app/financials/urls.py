"""
URL configuration for financial tracking API and HTML views.
"""

from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter
from invoicing_app.financials.views import (
    FinancialPeriodViewSet,
    RevenueCollectionViewSet,
    TaxLiabilityViewSet,
)
from invoicing_app.financials.views_html import (
    financial_dashboard,
    financial_periods_list,
    financial_period_detail,
    revenue_collections_list,
    revenue_collection_detail,
    tax_liabilities_list,
    tax_liability_detail,
    tax_liability_mark_remitted,
    tax_liability_create,
    tax_liability_edit,
)

app_name = "financials"

router = DefaultRouter()
router.register(r"periods", FinancialPeriodViewSet, basename="api-period")
router.register(r"revenue", RevenueCollectionViewSet, basename="api-revenue")
router.register(r"tax-liabilities", TaxLiabilityViewSet, basename="api-tax-liability")

urlpatterns = [
    # HTML views (PRIMARY - matched first)
    path("dashboard/", financial_dashboard, name="dashboard"),
    path("periods/list/", financial_periods_list, name="periods-list"),
    path("periods/<int:pk>/", financial_period_detail, name="period-detail"),
    path("revenue/list/", revenue_collections_list, name="revenue-list"),
    path("revenue/<int:pk>/", revenue_collection_detail, name="revenue-detail"),
    path("tax-liabilities/list/", tax_liabilities_list, name="tax-liabilities-list"),
    path("tax-liabilities/create/", tax_liability_create, name="tax-liability-create"),
    path(
        "tax-liabilities/<int:pk>/", tax_liability_detail, name="tax-liability-detail"
    ),
    path(
        "tax-liabilities/<int:pk>/edit/", tax_liability_edit, name="tax-liability-edit"
    ),
    path(
        "tax-liabilities/<int:pk>/mark-remitted/",
        tax_liability_mark_remitted,
        name="tax-liability-mark-remitted",
    ),
    # Redirect root paths to list views for user-friendly URLs
    path(
        "periods/",
        RedirectView.as_view(url="list/", permanent=False),
        name="periods-redirect",
    ),
    path(
        "revenue/",
        RedirectView.as_view(url="list/", permanent=False),
        name="revenue-redirect",
    ),
    path(
        "tax-liabilities/",
        RedirectView.as_view(url="list/", permanent=False),
        name="tax-liabilities-redirect",
    ),
    # API views (SECONDARY - for programmatic access)
    path("api/", include(router.urls)),
]
