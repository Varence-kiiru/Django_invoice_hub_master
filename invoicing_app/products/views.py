from rest_framework import viewsets, permissions
from invoicing_app.products.models import Product
from invoicing_app.core.permissions import IsReadOnlyOrAdmin
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """Product catalog with read access for all, write access for admins only."""

    queryset = Product.objects.filter(is_active=True).order_by("name")
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsReadOnlyOrAdmin]
    filterset_fields = ["sku", "name", "category"]
    search_fields = ["sku", "name"]

    def perform_create(self, serializer):
        """Capture the logged-in user for audit trail."""
        instance = serializer.save()
        instance._changed_by = self.request.user
        instance.save(update_fields=[])

    def perform_update(self, serializer):
        """Capture the logged-in user for audit trail."""
        instance = serializer.save()
        instance._changed_by = self.request.user
        instance.save(update_fields=[])
