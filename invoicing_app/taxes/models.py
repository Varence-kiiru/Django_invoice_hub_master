"""
Tax rates and VAT rules models.
"""
from django.db import models
from django.utils import timezone


class TaxRate(models.Model):
    """
    Master list of all applicable tax rates.
    Historical tracking: old rates kept with effective_to date.
    """
    TAX_TYPE_CHOICES = [
        ('vat', 'Value Added Tax (VAT)'),
        ('income_tax', 'Income Tax'),
        ('other', 'Other Tax'),
    ]

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(
        max_length=100,
        help_text="Display name (e.g., 'Standard VAT 16%')"
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Unique code (e.g., 'VATX16', 'VATZ00')"
    )
    rate_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Tax rate as percentage (e.g., 16.00, 0.00)"
    )
    tax_type = models.CharField(
        max_length=20,
        choices=TAX_TYPE_CHOICES,
        default='vat',
        db_index=True,
        help_text="Type of tax"
    )
    country = models.CharField(
        max_length=100,
        default='Kenya',
        help_text="Country this rate applies to"
    )
    effective_from = models.DateField(
        help_text="When this rate becomes effective"
    )
    effective_to = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When this rate expires (NULL = still active)"
    )
    is_vat_applicable = models.BooleanField(
        default=True,
        help_text="True if VAT can be recovered on purchases"
    )
    kra_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="KRA eTIMS tax type code (future)"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Additional details"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'taxes_taxrate'
        ordering = ['-effective_from', 'code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['tax_type']),
            models.Index(fields=['effective_from']),
            models.Index(fields=['effective_to']),
        ]

    def __str__(self):
        status = "active" if self.is_active() else "inactive"
        return f"{self.name} ({self.code}) - {status}"

    def is_active(self):
        """Check if this rate is currently active."""
        today = timezone.now().date()
        return self.effective_from <= today and (
            self.effective_to is None or today <= self.effective_to
        )

    def clean(self):
        """Validate effective dates."""
        from django.core.exceptions import ValidationError
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValidationError("effective_to must be >= effective_from")
        if self.rate_percentage < 0:
            raise ValidationError("rate_percentage must be >= 0")


class VATRule(models.Model):
    """
    Business rules for VAT applicability.
    Allows conditional VAT treatment (e.g., export goods = zero-rated).
    """
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(
        max_length=100,
        help_text="Rule description (e.g., 'Export goods - zero-rated')"
    )
    tax_class = models.ForeignKey(
        'products.ProductTaxClass',
        on_delete=models.CASCADE,
        related_name='vat_rules',
        help_text="Which tax class this rule applies to"
    )
    tax_rate = models.ForeignKey(
        TaxRate,
        on_delete=models.PROTECT,
        related_name='vat_rules',
        help_text="Which tax rate to apply"
    )
    condition = models.TextField(
        blank=True,
        null=True,
        help_text="Future: JSON condition (e.g., 'if customer.country != Kenya')"
    )
    priority = models.IntegerField(
        default=0,
        help_text="Higher priority rules evaluated first"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this rule is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'taxes_vatrule'
        ordering = ['-priority', 'name']
        indexes = [
            models.Index(fields=['tax_class']),
            models.Index(fields=['tax_rate']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        return f"{self.name} (priority: {self.priority})"
