from rest_framework import serializers
from invoicing_app.payments.models import Payment, PaymentMethod


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ["id", "name", "description", "is_active"]


class PaymentSerializer(serializers.ModelSerializer):
    payment_method = PaymentMethodSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "invoice",
            "amount",
            "payment_method",
            "payment_date",
            "transaction_reference",
            "status",
            "notes",
        ]

    def create(self, validated_data):
        payment = Payment.objects.create(**validated_data)
        # simple: update invoice amounts (could be deferred to signal)
        invoice = payment.invoice
        invoice.amount_paid = (invoice.amount_paid or 0) + payment.amount
        invoice.amount_due = invoice.total_amount - invoice.amount_paid
        if invoice.amount_due <= 0:
            invoice.status = "paid"
        invoice.save()
        return payment
