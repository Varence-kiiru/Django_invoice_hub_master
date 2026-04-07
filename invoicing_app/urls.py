"""Root URL configuration for invoicing_app with API router and auth."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Import drf-spectacular views for API documentation
try:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

    SPECTACULAR_AVAILABLE = True
except ImportError:
    SPECTACULAR_AVAILABLE = False

# Import viewsets
from invoicing_app.clients.views import ClientViewSet
from invoicing_app.products.views import ProductViewSet
from invoicing_app.invoices.views import InvoiceViewSet
from invoicing_app.payments.views import PaymentViewSet
from invoicing_app.taxes.views import TaxRateViewSet, VATRuleViewSet
from invoicing_app.quotations.views import QuoteViewSet
from invoicing_app.expenses.views import (
    ExpenseViewSet,
    ExpenseCategoryViewSet,
    VendorViewSet,
)
from invoicing_app.organizations.views import (
    OrganizationViewSet,
    OrganizationMemberViewSet,
    SubscriptionViewSet as OrgSubscriptionViewSet,
    InvoiceViewSet as OrgInvoiceViewSet,
)
from invoicing_app.core.views import UserViewSet
from invoicing_app.financials.views import (
    FinancialPeriodViewSet,
    RevenueCollectionViewSet,
    TaxLiabilityViewSet,
)
from invoicing_app.notifications.views import (
    EmailTemplateViewSet,
    NotificationLogViewSet,
)

router = routers.DefaultRouter()
router.register(r"clients", ClientViewSet)
router.register(r"products", ProductViewSet)
router.register(r"invoices", InvoiceViewSet)
router.register(r"payments", PaymentViewSet)
router.register(r"quotations", QuoteViewSet)
router.register(r"taxrates", TaxRateViewSet)
router.register(r"vatrules", VATRuleViewSet)
router.register(r"expense-categories", ExpenseCategoryViewSet)
router.register(r"vendors", VendorViewSet)
router.register(r"expenses", ExpenseViewSet)
router.register(r"organizations", OrganizationViewSet, basename="organization")
router.register(
    r"organization-members", OrganizationMemberViewSet, basename="organization-member"
)
router.register(r"subscriptions", OrgSubscriptionViewSet, basename="subscription")
router.register(r"billing-invoices", OrgInvoiceViewSet, basename="billing-invoice")
router.register(r"users", UserViewSet, basename="system-user")
router.register(r"users", UserViewSet, basename="user")
router.register(
    r"financial-periods", FinancialPeriodViewSet, basename="financial-period"
)
router.register(
    r"revenue-collections", RevenueCollectionViewSet, basename="revenue-collection"
)
router.register(r"tax-liabilities", TaxLiabilityViewSet, basename="tax-liability")
router.register(r"email-templates", EmailTemplateViewSet, basename="email-template")
router.register(r"notifications", NotificationLogViewSet, basename="notification-log")


# Service Worker view
def service_worker_view(request):
    """Serve service worker with correct content-type"""
    from django.http import FileResponse
    from django.conf import settings
    import os

    sw_path = os.path.join(settings.STATIC_ROOT, "js", "sw.js")
    if not os.path.exists(sw_path):
        # Try in staticfiles if collectstatic was run
        sw_path = os.path.join(settings.BASE_DIR, "static", "js", "sw.js")

    if os.path.exists(sw_path):
        response = FileResponse(
            open(sw_path, "rb"), content_type="application/javascript"
        )
        response["Cache-Control"] = "max-age=86400"  # Cache for 1 day
        return response

    from django.http import HttpResponse

    return HttpResponse("Service Worker Not Found", status=404)


urlpatterns = [
    path("admin/", admin.site.urls),
    # Service Worker - must be at root for scope
    path("sw.js", service_worker_view, name="service-worker"),
    # ━━━ Authentication ━━━
    path("auth/", include("invoicing_app.organizations.urls")),
    # ━━━ HTML Views - App Level URLs ━━━
    path("", include("invoicing_app.core.urls")),  # Auth, dashboard, reports, settings
    path("clients/", include("invoicing_app.clients.urls")),  # Client CRUD
    path("products/", include("invoicing_app.products.urls")),  # Product CRUD
    path("invoices/", include("invoicing_app.invoices.urls")),  # Invoice CRUD
    path("quotations/", include("invoicing_app.quotations.urls")),  # Quotations CRUD
    path("payments/", include("invoicing_app.payments.urls")),  # Payment CRUD
    path("deliveries/", include("invoicing_app.deliveries.urls")),  # Delivery CRUD
    path("expenses/", include("invoicing_app.expenses.urls")),  # Expense CRUD
    path("financials/", include("invoicing_app.financials.urls")),  # Financial tracking
    path("", include("invoicing_app.taxes.urls")),  # Tax Rates CRUD
    # REST API endpoints
    path("api/v1/", include(router.urls)),
    path("api/v1/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

# Add API Documentation endpoints (drf-spectacular)
if SPECTACULAR_AVAILABLE:
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(permission_classes=[AllowAny]), name="schema"),
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[AllowAny]),
            name="swagger-ui",
        ),
    ]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
