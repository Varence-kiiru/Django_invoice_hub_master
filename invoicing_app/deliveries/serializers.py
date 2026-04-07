"""Serializers for deliveries app REST API."""

from rest_framework import serializers
from invoicing_app.deliveries.models import Delivery, DeliveryLineItem


class DeliveryLineItemSerializer(serializers.ModelSerializer):
    """Serializer for delivery line items."""

    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = DeliveryLineItem
        fields = [
            "id",
            "product_name",
            "quantity_scheduled",
            "quantity_delivered",
            "unit",
            "notes",
            "shortfall",
            "is_fully_delivered",
        ]


class DeliverySerializer(serializers.ModelSerializer):
    """Serializer for deliveries."""

    invoice_number = serializers.CharField(
        source="invoice.invoice_number", read_only=True
    )
    client_name = serializers.CharField(source="invoice.client.name", read_only=True)
    line_items = DeliveryLineItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Delivery
        fields = [
            "id",
            "delivery_number",
            "invoice_number",
            "client_name",
            "status",
            "status_display",
            "scheduled_date",
            "actual_delivery_date",
            "delivery_method",
            "tracking_number",
            "condition",
            "line_items",
            "total_items_scheduled",
            "total_items_delivered",
            "is_fully_delivered",
        ]
