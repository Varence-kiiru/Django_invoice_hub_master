"""
Quotation models.
"""
from django.db import models
from django.utils import timezone
from invoicing_app.core.models import ActiveModel


class QuoteNumberSequence(models.Model):
    """
    Generates unique, non-gapped quote numbers per prefix/year.
    Uses SELECT FOR UPDATE for concurrent-safe incrementing.
    """
    id = models.BigAutoField(primary_key=True)
    prefix = models.CharField(
        max_length=20,
        default='QUOTE',
        help_text="Quote number prefix (QUOTE, PROPOSAL, etc.)"
    )
    year = models.IntegerField(
        help_text="Calendar year"
    )
    next_sequence = models.BigIntegerField(
        default=1,
        help_text="Next sequence number to use"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'quotations_quotenumbersequence'
        unique_together = [['prefix', 'year']]
        indexes = [
            models.Index(fields=['prefix', 'year']),
        ]

    def __str__(self):
        return f"{self.prefix}-{self.year}: next={self.next_sequence}"


class Quote(ActiveModel):
    """
    Sales quotation/proposal document.
    Structurally similar to Invoice but without payment tracking.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('sent', 'Sent to Client'),
        ('viewed', 'Viewed by Client'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
        ('converted', 'Converted to Invoice'),
        ('archived', 'Archived'),
    ]

    CURRENCY_CHOICES = [
        ('KES', 'Kenyan Shilling'),
        ('USD', 'US Dollar'),
    ]

    # ━━━ Identity ━━━
    quote_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Quote number (e.g., QUOTE-2026-0001)"
    )

    # ━━━ References ━━━
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.PROTECT,
        related_name='quotes',
        help_text="Client this quote is for"
    )

    # Related invoice if converted
    converted_invoice = models.OneToOneField(
        'invoices.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_quote',
        help_text="Invoice created from this quote"
    )

    # ━━━ Dates ━━━
    quote_date = models.DateField(
        default=timezone.now,
        db_index=True,
        help_text="Date quote was prepared"
    )
    valid_until = models.DateField(
        help_text="Quote expiration date"
    )

    # ━━━ Content ━━━
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Quote description/terms"
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='KES',
        help_text="Quote currency"
    )

    # ━━━ Status ━━━
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True,
        help_text="Quote status"
    )

    # ━━━ Denormalized Totals (Same as Invoice) ━━━
    subtotal_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Sum of line item amounts (excl. VAT)"
    )
    vat_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Total VAT"
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Subtotal + VAT"
    )

    # ━━━ Metadata ━━━
    issued_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When quote was formally issued"
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When quote was sent to client"
    )
    viewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When client viewed quote"
    )
    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When quote was accepted"
    )
    rejected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When quote was rejected"
    )
    expired_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When quote expired"
    )
    converted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When quote was converted to invoice"
    )
    rejection_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for rejection"
    )

    # ━━━ PDF Caching ━━━
    quote_pdf = models.FileField(
        upload_to='quotes/pdfs/',
        blank=True,
        null=True,
        help_text="Cached PDF file path"
    )

    # ━━━ Audit ━━━
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_quotes',
        help_text="User who created this quote"
    )
    updated_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_quotes',
        help_text="User who last updated this quote"
    )

    class Meta:
        db_table = 'quotations_quote'
        ordering = ['-quote_date', '-quote_number']
        indexes = [
            models.Index(fields=['quote_number']),
            models.Index(fields=['client']),
            models.Index(fields=['status']),
            models.Index(fields=['quote_date']),
            models.Index(fields=['valid_until']),
            models.Index(fields=['status', 'valid_until']),
        ]

    def __str__(self):
        return f"{self.quote_number} - {self.client.name} ({self.get_status_display()})"

    def clean(self):
        """Validate quote dates and amounts."""
        from django.core.exceptions import ValidationError
        if self.quote_date > self.valid_until:
            raise ValidationError("valid_until must be >= quote_date")
        if self.subtotal_amount < 0 or self.vat_amount < 0 or self.total_amount < 0:
            raise ValidationError("Amounts cannot be negative")
        if abs(self.total_amount - (self.subtotal_amount + self.vat_amount)) > 0.01:
            raise ValidationError("total_amount must equal subtotal + vat")

    def is_expired(self):
        """Check if quote has passed valid_until date."""
        return timezone.now().date() > self.valid_until and self.status not in ['converted', 'accepted', 'rejected']

    @property
    def days_until_expiry(self):
        """Days remaining until quote expires."""
        today = timezone.now().date()
        delta = (self.valid_until - today).days
        return max(0, delta)


class QuoteLineItem(models.Model):
    """
    Line items on a quote.
    Structurally identical to InvoiceLineItem.
    """
    id = models.BigAutoField(primary_key=True)
    quote = models.ForeignKey(
        Quote,
        on_delete=models.CASCADE,
        related_name='line_items',
        help_text="Quote this line item belongs to"
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quote_lines',
        help_text="Product (optional; if NULL, manual line item)"
    )
    description = models.CharField(
        max_length=500,
        help_text="Description (mandatory if product is NULL)"
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        help_text="Quantity"
    )
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Price per unit (excl. VAT)"
    )
    line_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="quantity × unit_price (excl. VAT)"
    )
    tax_rate = models.ForeignKey(
        'taxes.TaxRate',
        on_delete=models.PROTECT,
        related_name='quote_line_items',
        help_text="Which tax rate applies to this line"
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Calculated VAT (line_amount × tax_rate%)"
    )
    line_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="line_amount + tax_amount (incl. VAT)"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Line-item-specific notes"
    )
    sort_order = models.IntegerField(
        default=0,
        help_text="Display order"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quotations_quotelineitem'
        ordering = ['quote', 'sort_order', 'created_at']
        indexes = [
            models.Index(fields=['quote']),
            models.Index(fields=['product']),
            models.Index(fields=['tax_rate']),
            models.Index(fields=['quote', 'product']),
        ]

    def __str__(self):
        return f"{self.quote.quote_number} - {self.description[:30]}"

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

