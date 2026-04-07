"""
Expense tracking models for financial management.
Track business expenses, categories, and generate expense reports.
"""

from datetime import timedelta
from django.db import models
from django.conf import settings
from invoicing_app.core.models import BaseModel, TimeStampedModel


class ExpenseCategory(TimeStampedModel):
    """
    Expense category for organization.

    Examples: Office Supplies, Travel, Equipment, Utilities, etc.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Category name (e.g., Office Supplies, Travel, Utilities)",
    )
    description = models.TextField(
        blank=True, null=True, help_text="Category description"
    )
    is_active = models.BooleanField(default=True, help_text="Is this category active?")

    class Meta:
        db_table = "expenses_category"
        ordering = ["name"]
        verbose_name_plural = "Expense Categories"

    def __str__(self):
        return self.name


class Vendor(TimeStampedModel):
    """
    Vendor/Supplier information.

    Tracks who you buy from and payment terms.
    """

    name = models.CharField(max_length=255, unique=True, help_text="Vendor name")
    contact_email = models.EmailField(
        blank=True, null=True, help_text="Vendor contact email"
    )
    contact_phone = models.CharField(
        max_length=20, blank=True, null=True, help_text="Vendor phone number"
    )
    address = models.TextField(blank=True, null=True, help_text="Vendor address")
    payment_terms = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Payment terms (e.g., Net 30, Net 60)",
    )
    is_active = models.BooleanField(default=True, help_text="Is this vendor active?")

    class Meta:
        db_table = "expenses_vendor"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Expense(BaseModel):
    """
    Individual business expense record.

    Tracks what was spent, when, on what, and for what purpose.
    """

    PAYMENT_METHOD_CHOICES = [
        ("cash", "Cash"),
        ("bank_transfer", "Bank Transfer"),
        ("credit_card", "Credit Card"),
        ("check", "Check"),
        ("mpesa", "M-Pesa"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("paid", "Paid"),
    ]

    # Basic Information
    description = models.TextField(help_text="What was this expense for?")
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        related_name="expenses",
        help_text="Expense category",
    )
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expenses",
        help_text="Which vendor this expense is from",
    )

    # Amount Information
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Expense amount"
    )
    currency = models.CharField(
        max_length=3, default="KES", help_text="Currency code (e.g., USD, KES)"
    )

    # Date Information
    expense_date = models.DateField(help_text="When was this expense incurred?")
    submitted_date = models.DateField(
        null=True,
        blank=True,
        auto_now_add=True,
        help_text="When was this submitted for approval?",
    )
    approved_date = models.DateField(
        null=True, blank=True, help_text="When was this approved?"
    )
    paid_date = models.DateField(null=True, blank=True, help_text="When was this paid?")

    # Payment Information
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="bank_transfer",
        help_text="How was this expense paid?",
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Invoice/receipt number or reference",
    )

    # Status & Tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        db_index=True,
        help_text="Expense status",
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_expenses",
        help_text="Who submitted this expense",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_expenses",
        help_text="Who approved this expense",
    )

    # Additional Information
    notes = models.TextField(
        blank=True, null=True, help_text="Additional notes about this expense"
    )
    receipt_file = models.FileField(
        upload_to="receipts/%Y/%m/",
        blank=True,
        null=True,
        help_text="Receipt or invoice document",
    )
    is_reimbursable = models.BooleanField(
        default=False, help_text="Is this expense reimbursable to an employee?"
    )
    reimbursed_to = models.CharField(
        max_length=255, blank=True, null=True, help_text="Name of person to reimburse"
    )
    reimbursement_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount reimbursed",
    )

    class Meta:
        db_table = "expenses_expense"
        ordering = ["-expense_date", "-created_at"]
        indexes = [
            models.Index(fields=["category", "-expense_date"]),
            models.Index(fields=["status", "-expense_date"]),
            models.Index(fields=["vendor", "-expense_date"]),
        ]

    def __str__(self):
        return f"{self.description} - {self.amount} ({self.get_status_display()})"

    def can_be_edited(self):
        """Check if expense can be edited."""
        return self.status in ["draft", "submitted"]

    def can_be_approved(self):
        """Check if expense can be approved."""
        return self.status == "submitted"

    def can_be_paid(self):
        """Check if expense can be marked as paid."""
        return self.status == "approved"

    def get_display_amount(self):
        """Return formatted amount with currency."""
        return f"{self.currency} {self.amount:,.2f}"


class ExpenseBudget(TimeStampedModel):
    """
    Budget limits for expense categories.

    Track spending limits and monitor budget vs. actual.
    """

    category = models.OneToOneField(
        ExpenseCategory,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="budget",
        help_text="Expense category",
    )
    monthly_limit = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Monthly budget limit"
    )
    annual_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annual budget limit (optional)",
    )
    alert_threshold = models.IntegerField(
        default=80, help_text="Alert when spending reaches this % of limit"
    )

    class Meta:
        db_table = "expenses_budget"
        verbose_name_plural = "Expense Budgets"

    def __str__(self):
        return f"{self.category.name} Budget"

    def get_monthly_spent(self):
        """Get this month's spending in this category."""
        from django.utils import timezone
        from django.db.models import Sum

        current_month = timezone.now().date().replace(day=1)
        next_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)

        expenses = Expense.objects.filter(
            category=self.category,
            expense_date__gte=current_month,
            expense_date__lt=next_month,
            status__in=["submitted", "approved", "paid"],
        ).aggregate(total=Sum("amount"))

        return expenses["total"] or 0

    def is_over_budget(self):
        """Check if category is over monthly limit."""
        return self.get_monthly_spent() > self.monthly_limit

    def is_alert_threshold_reached(self):
        """Check if spending reached alert threshold."""
        spent = self.get_monthly_spent()
        threshold_amount = (self.monthly_limit * self.alert_threshold) / 100
        return spent >= threshold_amount
