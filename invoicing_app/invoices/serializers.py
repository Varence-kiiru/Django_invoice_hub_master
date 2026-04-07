from rest_framework import serializers
from invoicing_app.invoices.models import Invoice, InvoiceLineItem
from invoicing_app.taxes.services import TaxCalculationService


class InvoiceLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLineItem
        fields = [
            "id",
            "description",
            "product",
            "quantity",
            "unit_price",
            "line_amount",
            "tax_rate",
            "tax_amount",
            "line_total",
            "notes",
            "sort_order",
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    line_items = InvoiceLineItemSerializer(many=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "client",
            "invoice_date",
            "due_date",
            "status",
            "description",
            "currency",
            "subtotal_amount",
            "vat_amount",
            "total_amount",
            "amount_paid",
            "amount_due",
            "line_items",
            "created_at",
        ]
        read_only_fields = [
            "subtotal_amount",
            "vat_amount",
            "total_amount",
            "amount_due",
        ]

    def create(self, validated_data):
        items = validated_data.pop("line_items", [])
        invoice = Invoice.objects.create(**validated_data)
        # create line items and compute totals
        for li in items:
            InvoiceLineItem.objects.create(invoice=invoice, **li)
        # Recalculate totals
        totals = TaxCalculationService.calculate_invoice_totals(
            invoice.line_items.all()
        )
        invoice.subtotal_amount = totals["subtotal"]
        invoice.vat_amount = totals["vat_amount"]
        invoice.total_amount = totals["total"]
        invoice.amount_due = invoice.total_amount - invoice.amount_paid
        invoice.save()
        return invoice

    def update(self, instance, validated_data):
        items = validated_data.pop("line_items", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if items is not None:
            instance.line_items.all().delete()
            for li in items:
                InvoiceLineItem.objects.create(invoice=instance, **li)
        totals = TaxCalculationService.calculate_invoice_totals(
            instance.line_items.all()
        )
        instance.subtotal_amount = totals["subtotal"]
        instance.vat_amount = totals["vat_amount"]
        instance.total_amount = totals["total"]
        instance.amount_due = instance.total_amount - instance.amount_paid
        instance.save()
        return instance
