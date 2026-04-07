"""
Invoice models.
"""

from django.db import models
from django.utils import timezone
from invoicing_app.core.models import ActiveModel


class InvoiceNumberSequence(models.Model):
    """
    Generates unique, non-gapped invoice numbers per prefix/year.
    Uses SELECT FOR UPDATE for concurrent-safe incrementing.
    """

    id = models.BigAutoField(primary_key=True)
    prefix = models.CharField(
        max_length=20,
        default="OG-INV",
        help_text="Invoice number prefix (OG-INV, QUOTE, PROFORMA, etc.)",
    )
    year = models.IntegerField(help_text="Calendar year")
    next_sequence = models.BigIntegerField(
        default=1, help_text="Next sequence number to use"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "invoices_invoicenumbersequence"
        unique_together = [["prefix", "year"]]
        indexes = [
            models.Index(fields=["prefix", "year"]),
        ]

    def __str__(self):
        return f"{self.prefix}-{self.year}: next={self.next_sequence}"


class Invoice(ActiveModel):
    """
    Invoice header with financial totals and status tracking.
    Denormalized totals for query performance; recalculated on line item changes.
    """

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("issued", "Issued"),
        ("sent", "Sent to Client"),
        ("viewed", "Viewed by Client"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
        ("cancelled", "Cancelled"),
    ]

    CURRENCY_CHOICES = [
        ("KES", "Kenyan Shilling"),
        ("USD", "US Dollar"),
    ]

    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Invoice number (e.g., INV-2026-0001)",
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.PROTECT,
        related_name="invoices",
        help_text="Client this invoice is for",
    )
    invoice_date = models.DateField(
        default=timezone.now, db_index=True, help_text="Invoice date"
    )
    due_date = models.DateField(help_text="Payment due date")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        db_index=True,
        help_text="Invoice status",
    )
    description = models.TextField(
        blank=True, null=True, help_text="Optional memo/description"
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default="KES",
        help_text="Invoice currency",
    )

    # Denormalized totals (recalculated on line item save)
    subtotal_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Sum of all line item amounts (excl. VAT)",
    )
    vat_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Total VAT on all line items",
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Subtotal + VAT (total to pay)",
    )
    amount_paid = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Sum of all payments received",
    )
    amount_due = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, help_text="Total - amount_paid"
    )

    # Metadata timestamps
    issued_at = models.DateTimeField(
        null=True, blank=True, help_text="When invoice was formally issued"
    )
    sent_at = models.DateTimeField(
        null=True, blank=True, help_text="When PDF was sent to client"
    )
    viewed_at = models.DateTimeField(
        null=True, blank=True, help_text="When client opened email/clicked link"
    )
    first_reminder_sent_at = models.DateTimeField(
        null=True, blank=True, help_text="When first payment reminder was sent"
    )
    second_reminder_sent_at = models.DateTimeField(
        null=True, blank=True, help_text="When second payment reminder was sent"
    )
    cancelled_at = models.DateTimeField(
        null=True, blank=True, help_text="When invoice was cancelled"
    )
    cancellation_reason = models.TextField(
        blank=True, null=True, help_text="Reason for cancellation"
    )
    paid_at = models.DateTimeField(
        null=True, blank=True, help_text="When invoice was fully paid"
    )

    # PDF storage for caching
    invoice_pdf = models.FileField(
        upload_to="invoices/pdfs/",
        blank=True,
        null=True,
        help_text="Cached PDF file path",
    )

    # Audit fields
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_invoices",
        help_text="User who created this invoice",
    )
    updated_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_invoices",
        help_text="User who last updated this invoice",
    )

    class Meta:
        db_table = "invoices_invoice"
        ordering = ["-invoice_date", "-invoice_number"]
        indexes = [
            models.Index(fields=["invoice_number"]),
            models.Index(fields=["client"]),
            models.Index(fields=["status"]),
            models.Index(fields=["invoice_date"]),
            models.Index(fields=["due_date"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["status", "due_date"]),
        ]

    def __str__(self):
        return (
            f"{self.invoice_number} - {self.client.name} ({self.get_status_display()})"
        )

    def clean(self):
        """Validate invoice dates and amounts."""
        from django.core.exceptions import ValidationError

        if self.invoice_date > self.due_date:
            raise ValidationError("due_date must be >= invoice_date")
        if self.subtotal_amount < 0 or self.vat_amount < 0 or self.total_amount < 0:
            raise ValidationError("Amounts cannot be negative")
        if abs(self.total_amount - (self.subtotal_amount + self.vat_amount)) > 0.01:
            raise ValidationError("total_amount must equal subtotal + vat")
        if self.amount_paid < 0:
            raise ValidationError("amount_paid cannot be negative")
        expected_due = self.total_amount - self.amount_paid
        if abs(self.amount_due - expected_due) > 0.01:
            raise ValidationError("amount_due must equal total - amount_paid")

    def is_overdue(self):
        """Check if invoice is overdue."""
        today = timezone.now().date()
        return self.status in ["issued", "sent", "viewed"] and today > self.due_date

    @property
    def days_until_due(self):
        """Calculate days until due date (returns 0 or negative if overdue)."""
        today = timezone.now().date()
        delta = (self.due_date - today).days
        return max(0, delta)  # Return 0 if overdue

    @property
    def days_overdue(self):
        """Calculate days overdue (returns 0 if not overdue)."""
        today = timezone.now().date()
        if today > self.due_date:
            return (today - self.due_date).days
        return 0


class InvoiceLineItem(models.Model):
    """
    Line items on an invoice.
    VAT calculated based on tax_rate and line_amount.
    """

    id = models.BigAutoField(primary_key=True)
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="line_items",
        help_text="Invoice this line item belongs to",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoice_lines",
        help_text="Product (optional; if NULL, manual line item)",
    )
    description = models.CharField(
        max_length=500, help_text="Description (mandatory if product is NULL)"
    )
    quantity = models.DecimalField(
        max_digits=12, decimal_places=4, help_text="Quantity"
    )
    unit_price = models.DecimalField(
        max_digits=15, decimal_places=2, help_text="Price per unit (excl. VAT)"
    )
    line_amount = models.DecimalField(
        max_digits=15, decimal_places=2, help_text="quantity × unit_price (excl. VAT)"
    )
    tax_rate = models.ForeignKey(
        "taxes.TaxRate",
        on_delete=models.PROTECT,
        related_name="invoice_line_items",
        help_text="Which tax rate applies to this line",
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Calculated VAT (line_amount × tax_rate%)",
    )
    line_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="line_amount + tax_amount (incl. VAT)",
    )
    notes = models.TextField(
        blank=True, null=True, help_text="Line-item-specific notes"
    )
    sort_order = models.IntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "invoices_invoicelineitem"
        ordering = ["invoice", "sort_order", "created_at"]
        indexes = [
            models.Index(fields=["invoice"]),
            models.Index(fields=["product"]),
            models.Index(fields=["tax_rate"]),
            models.Index(fields=["invoice", "product"]),
        ]

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.description[:30]}"

    def clean(self):
        """Validate line item amounts."""
        from django.core.exceptions import ValidationError

        if self.quantity <= 0:
            raise ValidationError("quantity must be > 0")
        if self.unit_price < 0:
            raise ValidationError("unit_price must be >= 0")
        expected_line_amount = self.quantity * self.unit_price
        if abs(self.line_amount - expected_line_amount) > 0.01:
            raise ValidationError("line_amount must equal quantity × unit_price")
        expected_tax = self.line_amount * (self.tax_rate.rate_percentage / 100)
        if abs(self.tax_amount - expected_tax) > 0.01:
            raise ValidationError("tax_amount must equal line_amount × rate%")
        expected_total = self.line_amount + self.tax_amount
        if abs(self.line_total - expected_total) > 0.01:
            raise ValidationError("line_total must equal line_amount + tax_amount")
