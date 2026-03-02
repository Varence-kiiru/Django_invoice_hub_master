"""Root URL configuration for invoicing_app with API router and auth."""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.views.decorators.cache import cache_page
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Import viewsets
from invoicing_app.clients.views import ClientViewSet
from invoicing_app.products.views import ProductViewSet
from invoicing_app.invoices.views import InvoiceViewSet
from invoicing_app.payments.views import PaymentViewSet
from invoicing_app.taxes.views import TaxRateViewSet, VATRuleViewSet
from invoicing_app.quotations.views import QuoteViewSet
from invoicing_app.expenses.views import ExpenseViewSet, ExpenseCategoryViewSet, VendorViewSet

router = routers.DefaultRouter()
router.register(r'clients', ClientViewSet)
router.register(r'products', ProductViewSet)
router.register(r'invoices', InvoiceViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'quotations', QuoteViewSet)
router.register(r'taxrates', TaxRateViewSet)
router.register(r'vatrules', VATRuleViewSet)
router.register(r'expense-categories', ExpenseCategoryViewSet)
router.register(r'vendors', VendorViewSet)
router.register(r'expenses', ExpenseViewSet)


# Service Worker view  
def service_worker_view(request):
    """Serve service worker with correct content-type"""
    from django.http import FileResponse
    from django.conf import settings
    import os
    
    sw_path = os.path.join(settings.STATIC_ROOT, 'js', 'sw.js')
    if not os.path.exists(sw_path):
        # Try in staticfiles if collectstatic was run
        sw_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'sw.js')
    
    if os.path.exists(sw_path):
        response = FileResponse(open(sw_path, 'rb'), content_type='application/javascript')
        response['Cache-Control'] = 'max-age=86400'  # Cache for 1 day
        return response
    
    from django.http import HttpResponse
    return HttpResponse('Service Worker Not Found', status=404)


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Service Worker - must be at root for scope
    path('sw.js', service_worker_view, name='service-worker'),
    
    # ━━━ HTML Views - App Level URLs ━━━
    path('', include('invoicing_app.core.urls')),           # Auth, dashboard, reports, settings
    path('clients/', include('invoicing_app.clients.urls')), # Client CRUD
    path('products/', include('invoicing_app.products.urls')), # Product CRUD
    path('invoices/', include('invoicing_app.invoices.urls')), # Invoice CRUD
    path('quotations/', include('invoicing_app.quotations.urls')), # Quotations CRUD
    path('payments/', include('invoicing_app.payments.urls')), # Payment CRUD
    path('expenses/', include('invoicing_app.expenses.urls')), # Expense CRUD
    path('', include('invoicing_app.taxes.urls')),          # Tax Rates CRUD
    
    # REST API endpoints
    path('api/v1/', include((router.urls, 'api'), namespace='v1')),
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# Serve media files in development
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
