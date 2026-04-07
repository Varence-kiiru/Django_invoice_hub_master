from rest_framework import viewsets, permissions
from invoicing_app.taxes.models import TaxRate, VATRule
from .serializers import TaxRateSerializer, VATRuleSerializer


class TaxRateViewSet(viewsets.ModelViewSet):
    queryset = TaxRate.objects.all().order_by("-effective_from")
    serializer_class = TaxRateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["code", "is_vat_applicable"]
    search_fields = ["code", "name"]


class VATRuleViewSet(viewsets.ModelViewSet):
    queryset = VATRule.objects.all().order_by("priority")
    serializer_class = VATRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["tax_class", "tax_rate", "is_active"]
