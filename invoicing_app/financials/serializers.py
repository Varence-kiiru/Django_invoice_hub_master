"""
Serializers for financial tracking API.
"""

from rest_framework import serializers
from invoicing_app.financials.models import (
    RevenueCollection,
    TaxLiability,
    FinancialPeriod,
)


class FinancialPeriodSerializer(serializers.ModelSerializer):
    """Serializer for FinancialPeriod."""

    period_type_display = serializers.CharField(
        source="get_period_type_display", read_only=True
    )

    class Meta:
        model = FinancialPeriod
        fields = [
            "id",
            "period_type",
            "period_type_display",
            "start_date",
            "end_date",
            "is_closed",
            "closed_at",
        ]


class RevenueCollectionSerializer(serializers.ModelSerializer):
    """Serializer for RevenueCollection."""

    invoice_number = serializers.CharField(
        source="invoice.invoice_number", read_only=True
    )
    payment_reference = serializers.CharField(
        source="payment.receipt_number", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = RevenueCollection
        fields = [
            "id",
            "collected_date",
            "invoice_number",
            "payment_reference",
            "revenue_amount",
            "tax_amount",
            "total_amount",
            "tax_type",
            "tax_rate",
            "status",
            "status_display",
            "remitted_date",
        ]


class TaxLiabilitySerializer(serializers.ModelSerializer):
    """Serializer for TaxLiability."""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    period_display = serializers.CharField(
        source="financial_period.__str__", read_only=True
    )
    days_until_due = serializers.SerializerMethodField()

    class Meta:
        model = TaxLiability
        fields = [
            "id",
            "tax_type",
            "period_display",
            "total_revenue",
            "total_tax_collected",
            "status",
            "status_display",
            "due_date",
            "remitted_date",
            "final_liability",
            "days_until_due",
        ]

    def get_days_until_due(self, obj):
        """Calculate days until tax is due."""
        if obj.due_date:
            from datetime import date

            today = date.today()
            return (obj.due_date - today).days
        return None
