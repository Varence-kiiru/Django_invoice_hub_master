"""
Payment models.
"""

from django.db import models
from django.utils import timezone


class PaymentReceiptNumberSequence(models.Model):
    """
    Generates unique, non-gapped payment receipt numbers per prefix/year.
    Uses SELECT FOR UPDATE for concurrent-safe incrementing.
    """

    id = models.BigAutoField(primary_key=True)
    prefix = models.CharField(
        max_length=20,
        default="REC",
        help_text="Payment receipt number prefix (REC, RCPT, etc.)",
    )
    year = models.IntegerField(help_text="Calendar year")
    next_sequence = models.BigIntegerField(
        default=1, help_text="Next sequence number to use"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payments_receiptnumbersequence"
        unique_together = [["prefix", "year"]]
        indexes = [
            models.Index(fields=["prefix", "year"]),
        ]

    def __str__(self):
        return f"{self.prefix}-{self.year} (next: {self.next_sequence})"


class PaymentMethod(models.Model):
    """
    Available payment methods (Cash, Bank Transfer, M-Pesa, Cheque, etc.).
    """

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(
        max_length=100, unique=True, db_index=True, help_text="Payment method name"
    )
    description = models.TextField(blank=True, null=True, help_text="Description")
    is_active = models.BooleanField(
        default=True, db_index=True, help_text="Whether this method is available"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payments_paymentmethod"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name


class Payment(models.Model):
    """
    Payment record for an invoice.
    Tracks partial payments and status.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("failed", "Failed"),
        ("reversed", "Reversed"),
    ]

    id = models.BigAutoField(primary_key=True)
    receipt_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        null=True,
        blank=True,
        help_text="Receipt number (e.g., REC-2026-0001)",
    )
    receipt_pdf = models.FileField(
        upload_to="payments/receipts/",
        null=True,
        blank=True,
        help_text="Generated PDF receipt file",
    )
    invoice = models.ForeignKey(
        "invoices.Invoice",
        on_delete=models.PROTECT,
        related_name="payments",
        help_text="Invoice this payment is for",
    )
    amount = models.DecimalField(
        max_digits=15, decimal_places=2, help_text="Payment amount"
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        related_name="payments",
        help_text="How was this payment made?",
    )
    payment_date = models.DateField(
        default=timezone.now, db_index=True, help_text="Date payment was received"
    )
    transaction_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text="External reference (M-Pesa ref, cheque number, bank ref)",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
        help_text="Payment status",
    )
    notes = models.TextField(blank=True, null=True, help_text="Internal notes")
    recorded_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_payments",
        help_text="User who recorded this payment",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments_payment"
        ordering = ["-payment_date", "-created_at"]
        indexes = [
            models.Index(fields=["invoice"]),
            models.Index(fields=["payment_method"]),
            models.Index(fields=["payment_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["transaction_reference"]),
        ]

    def __str__(self):
        return f"Payment of {self.amount} for {self.invoice.invoice_number}"

    def clean(self):
        """Validate payment amount and date."""
        from django.core.exceptions import ValidationError

        if self.amount <= 0:
            raise ValidationError("amount must be > 0")
        # Check amount doesn't exceed invoice total
        if self.amount > self.invoice.total_amount:
            raise ValidationError(
                f"Payment cannot exceed invoice total ({self.invoice.total_amount})"
            )
        # Check payment_date is not in the future
        if self.payment_date > timezone.now().date():
            raise ValidationError("payment_date cannot be in the future")


class PaymentReconciliation(models.Model):
    """
    Audit trail for payment-to-invoice matching.
    Tracks how payments are applied to invoices.
    """

    id = models.BigAutoField(primary_key=True)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="reconciliations",
        help_text="Payment being reconciled",
    )
    invoice = models.ForeignKey(
        "invoices.Invoice",
        on_delete=models.CASCADE,
        related_name="payment_reconciliations",
        help_text="Invoice this payment is for",
    )
    amount_matched = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Amount applied from this payment to this invoice",
    )
    matched_at = models.DateTimeField(
        default=timezone.now, help_text="When this reconciliation occurred"
    )
    reconciled_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reconciled_payments",
        help_text="User who performed reconciliation",
    )
    notes = models.TextField(blank=True, null=True, help_text="Reconciliation notes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payments_paymentreconciliation"
        ordering = ["-matched_at"]
        indexes = [
            models.Index(fields=["payment"]),
            models.Index(fields=["invoice"]),
        ]

    def __str__(self):
        return f"Reconciliation: {self.amount_matched} - {self.payment.invoice.invoice_number}"

    def clean(self):
        """Validate amount_matched <= payment.amount."""
        from django.core.exceptions import ValidationError

        if self.amount_matched <= 0:
            raise ValidationError("amount_matched must be > 0")
        if self.amount_matched > self.payment.amount:
            raise ValidationError("amount_matched cannot exceed payment amount")
