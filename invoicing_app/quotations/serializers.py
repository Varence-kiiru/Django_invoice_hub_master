"""
REST API serializers for Quotations.
"""
from rest_framework import serializers
from .models import Quote, QuoteLineItem


class QuoteLineItemSerializer(serializers.ModelSerializer):
    """Serializer for quote line items."""

    class Meta:
        model = QuoteLineItem
        fields = [
            'id', 'description', 'product', 'quantity', 'unit_price',
            'line_amount', 'tax_rate', 'tax_amount', 'line_total',
            'notes', 'sort_order'
        ]


class QuoteSerializer(serializers.ModelSerializer):
    """Serializer for quotes with nested line items."""
    line_items = QuoteLineItemSerializer(many=True, read_only=True)
    days_until_expiry = serializers.SerializerMethodField()

    class Meta:
        model = Quote
        fields = [
            'id', 'quote_number', 'client', 'quote_date', 'valid_until',
            'status', 'description', 'currency', 'subtotal_amount',
            'vat_amount', 'total_amount', 'line_items', 'created_at',
            'converted_invoice', 'days_until_expiry'
        ]
        read_only_fields = [
            'quote_number', 'subtotal_amount', 'vat_amount',
            'total_amount', 'converted_invoice'
        ]

    def get_days_until_expiry(self, obj):
        """Get days until quote expires."""
        return obj.days_until_expiry


class QuoteConvertSerializer(serializers.Serializer):
    """Serializer for converting quote to invoice."""
    invoice_date = serializers.DateField(required=False)
    due_date = serializers.DateField(required=True)
