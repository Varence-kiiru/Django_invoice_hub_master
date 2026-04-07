"""
Financial tracking models for revenue collection and tax liability management.
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal


class FinancialPeriod(models.Model):
    """
    Fiscal period for tax and financial reporting.
    Allows fine-grained control over reporting periods.
    """

    PERIOD_TYPE_CHOICES = [
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("semi_annual", "Semi-Annual"),
        ("annual", "Annual"),
    ]

    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="financial_periods",
        help_text="Organization this period belongs to",
    )
    period_type = models.CharField(
        max_length=20,
        choices=PERIOD_TYPE_CHOICES,
        default="monthly",
        help_text="Type of fiscal period",
    )
    start_date = models.DateField(help_text="Period start date", db_index=True)
    end_date = models.DateField(help_text="Period end date", db_index=True)
    is_closed = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether period is closed for reporting",
    )
    closed_at = models.DateTimeField(
        null=True, blank=True, help_text="When period was closed"
    )
    notes = models.TextField(blank=True, null=True, help_text="Period notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "financials_financialperiod"
        ordering = ["-start_date"]
        unique_together = ("organization", "start_date", "end_date")
        indexes = [
            models.Index(fields=["organization", "start_date"]),
            models.Index(fields=["organization", "is_closed"]),
        ]

    def __str__(self):
        if self.period_type == "monthly":
            return self.start_date.strftime("%B %Y")
        if self.period_type == "quarterly":
            quarter = (self.start_date.month - 1) // 3 + 1
            return f"Q{quarter} {self.start_date.year}"
        if self.period_type == "annual":
            return str(self.start_date.year)
        return (
            f"{self.get_period_type_display()} {self.start_date.strftime('%Y-%m-%d')}"
        )


class RevenueCollection(models.Model):
    """
    Individual revenue record created when a payment is confirmed.
    Tracks collected revenue by invoice with tax breakdown.
    """

    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="revenue_collections",
        help_text="Organization that received payment",
    )
    payment = models.OneToOneField(
        "payments.Payment",
        on_delete=models.CASCADE,
        related_name="revenue_collection",
        help_text="Payment that generated this revenue",
    )
    invoice = models.ForeignKey(
        "invoices.Invoice",
        on_delete=models.CASCADE,
        related_name="revenue_collections",
        help_text="Invoice this payment is for",
    )
    financial_period = models.ForeignKey(
        FinancialPeriod,
        on_delete=models.PROTECT,
        related_name="revenue_collections",
        help_text="Financial period this revenue belongs to",
    )
    collected_date = models.DateField(
        default=timezone.now, db_index=True, help_text="Date revenue was collected"
    )
    # Revenue breakdown
    revenue_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Revenue collected (excl. tax)",
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Tax collected on this revenue",
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Total collected (revenue + tax)",
    )
    # Tax tracking
    tax_type = models.CharField(
        max_length=50,
        default="VAT",
        help_text="Type of tax (VAT, Withholding, etc.)",
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Tax rate applied (%)",
    )
    # Remittance tracking
    status = models.CharField(
        max_length=20,
        default="collected",
        choices=[
            ("collected", "Collected"),
            ("pending_remittance", "Pending Remittance"),
            ("remitted", "Remitted"),
            ("disputed", "Disputed"),
        ],
        db_index=True,
        help_text="Revenue/tax status",
    )
    remitted_date = models.DateField(
        null=True, blank=True, help_text="Date tax was remitted"
    )
    remittance_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Tax office remittance reference/receipt",
    )
    notes = models.TextField(blank=True, null=True, help_text="Collection notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "financials_revenuecollection"
        ordering = ["-collected_date"]
        indexes = [
            models.Index(fields=["organization", "collected_date"]),
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "tax_type"]),
            models.Index(fields=["financial_period", "status"]),
        ]

    def __str__(self):
        return f"Revenue {self.invoice.invoice_number} - {self.total_amount}"


class TaxLiability(models.Model):
    """
    Aggregated tax liability by period and tax type.
    Automatically calculated from RevenueCollection records.
    Used for tax remittance management and reporting.
    """

    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="tax_liabilities",
        help_text="Organization with tax liability",
    )
    financial_period = models.ForeignKey(
        FinancialPeriod,
        on_delete=models.CASCADE,
        related_name="tax_liabilities",
        help_text="Financial period this liability covers",
    )
    tax_type = models.CharField(
        max_length=50,
        default="VAT",
        db_index=True,
        help_text="Type of tax (VAT, Withholding, etc.)",
    )
    # Liability amounts
    total_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Total revenue collected in period",
    )
    total_tax_collected = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Total tax collected in period",
    )
    # Remittance status
    status = models.CharField(
        max_length=20,
        default="pending",
        choices=[
            ("pending", "Pending"),
            ("due_soon", "Due Soon"),
            ("overdue", "Overdue"),
            ("remitted", "Remitted"),
            ("disputed", "Disputed"),
        ],
        db_index=True,
        help_text="Liability status",
    )
    due_date = models.DateField(
        null=True, blank=True, help_text="Tax remittance due date"
    )
    remitted_date = models.DateField(
        null=True, blank=True, help_text="Date tax was actually remitted"
    )
    remittance_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Tax office remittance reference/receipt number",
    )
    # Penalties/discounts
    penalties = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Late payment penalties",
    )
    discounts = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Tax credits/discounts",
    )
    final_liability = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Final amount after penalties/discounts",
    )
    notes = models.TextField(blank=True, null=True, help_text="Liability notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "financials_taxliability"
        ordering = ["-financial_period", "tax_type"]
        unique_together = ("financial_period", "tax_type", "organization")
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "due_date"]),
        ]

    def __str__(self):
        return f"{self.tax_type} {self.financial_period} - {self.total_tax_collected}"
