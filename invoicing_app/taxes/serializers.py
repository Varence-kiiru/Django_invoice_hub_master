from rest_framework import serializers
from invoicing_app.taxes.models import TaxRate, VATRule


class TaxRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxRate
        fields = ['id', 'code', 'name', 'rate_percentage', 'effective_from', 'effective_to', 'is_vat_applicable']


class VATRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = VATRule
        fields = ['id', 'tax_class', 'tax_rate', 'priority', 'is_active']
