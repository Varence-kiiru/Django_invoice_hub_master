"""
Django admin configuration for financial tracking.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from datetime import date
from invoicing_app.financials.models import (
    FinancialPeriod,
    RevenueCollection,
    TaxLiability,
)


@admin.register(FinancialPeriod)
class FinancialPeriodAdmin(admin.ModelAdmin):
    """Admin interface for FinancialPeriod."""

    list_display = [
        "period_display",
        "organization",
        "start_date",
        "end_date",
        "status_badge",
        "total_revenue",
    ]
    list_filter = ("period_type", "is_closed", "start_date", "organization")
    search_fields = ("organization__name",)
    readonly_fields = ("created_at", "updated_at", "period_display")
    date_hierarchy = "start_date"
    fieldsets = (
        (
            "Period Information",
            {
                "fields": (
                    "organization",
                    "period_type",
                    "period_display",
                    "start_date",
                    "end_date",
                )
            },
        ),
        ("Status", {"fields": ("is_closed", "closed_at")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def period_display(self, obj):
        """Display formatted period."""
        return f"{obj.get_period_type_display()} {obj.start_date.year}"

    period_display.short_description = "Period"

    def status_badge(self, obj):
        """Display status as colored badge."""
        if obj.is_closed:
            return format_html(
                '<span style="color: white; background-color: green; padding: 3px 8px; border-radius: 3px;">Closed</span>'
            )
        return format_html(
            '<span style="color: white; background-color: blue; padding: 3px 8px; border-radius: 3px;">Open</span>'
        )

    status_badge.short_description = "Status"

    def total_revenue(self, obj):
        """Display total revenue for period."""
        total = obj.taxliability_set.aggregate(total=Sum("total_revenue"))["total"] or 0
        return f"KES {total:,.2f}"

    total_revenue.short_description = "Total Revenue"


@admin.register(RevenueCollection)
class RevenueCollectionAdmin(admin.ModelAdmin):
    """Admin interface for RevenueCollection."""

    list_display = [
        "id",
        "collected_date",
        "invoice_number",
        "revenue_display",
        "tax_display",
        "tax_type",
        "status_badge",
    ]
    list_filter = (
        "status",
        "tax_type",
        "collected_date",
        "organization",
    )
    search_fields = (
        "invoice__invoice_number",
        "payment__receipt_number",
        "organization__name",
    )
    readonly_fields = (
        "financial_period",
        "created_at",
        "updated_at",
        "total_amount",
        "invoice_number",
        "payment_reference",
    )
    date_hierarchy = "collected_date"
    fieldsets = (
        (
            "Collection Details",
            {
                "fields": (
                    "organization",
                    "collected_date",
                    "invoice_number",
                    "payment_reference",
                    "financial_period",
                )
            },
        ),
        (
            "Financial Breakdown",
            {
                "fields": (
                    "revenue_amount",
                    "tax_amount",
                    "total_amount",
                    "tax_type",
                    "tax_rate",
                )
            },
        ),
        (
            "Status",
            {"fields": ("status", "remitted_date")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def invoice_number(self, obj):
        """Display invoice number."""
        return obj.invoice.invoice_number if obj.invoice else "N/A"

    invoice_number.short_description = "Invoice"

    def payment_reference(self, obj):
        """Display payment reference."""
        return obj.payment.receipt_number if obj.payment else "N/A"

    payment_reference.short_description = "Payment Ref"

    def revenue_display(self, obj):
        """Display revenue amount formatted."""
        return f"KES {obj.revenue_amount:,.2f}"

    revenue_display.short_description = "Revenue"

    def tax_display(self, obj):
        """Display tax amount formatted."""
        return f"KES {obj.tax_amount:,.2f}"

    tax_display.short_description = "Tax"

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            "collected": "green",
            "pending": "orange",
            "remitted": "blue",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            f'<span style="color: white; background-color: {color}; padding: 3px 8px; border-radius: 3px;">{obj.get_status_display()}</span>'
        )

    status_badge.short_description = "Status"


@admin.register(TaxLiability)
class TaxLiabilityAdmin(admin.ModelAdmin):
    """Admin interface for TaxLiability."""

    list_display = [
        "tax_type",
        "period",
        "total_tax_collected",
        "status_badge",
        "due_date",
        "days_until_due_display",
    ]
    list_filter = (
        "status",
        "tax_type",
        "financial_period__start_date",
        "organization",
    )
    search_fields = (
        "tax_type",
        "organization__name",
    )
    readonly_fields = (
        "total_revenue",
        "total_tax_collected",
        "created_at",
        "updated_at",
        "period",
    )
    date_hierarchy = "financial_period__start_date"
    fieldsets = (
        (
            "Liability Details",
            {
                "fields": (
                    "organization",
                    "period",
                    "tax_type",
                    "total_revenue",
                    "total_tax_collected",
                )
            },
        ),
        (
            "Remittance",
            {
                "fields": (
                    "status",
                    "due_date",
                    "remitted_date",
                    "remittance_reference",
                    "final_liability",
                )
            },
        ),
        ("Adjustments", {"fields": ("penalties", "discounts")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def period(self, obj):
        """Display period."""
        return str(obj.financial_period)

    period.short_description = "Period"

    def total_tax_collected(self, obj):
        """Display total tax collected formatted."""
        return f"KES {obj.total_tax_collected:,.2f}"

    total_tax_collected.short_description = "Tax Collected"

    def total_revenue(self, obj):
        """Display total revenue formatted."""
        return f"KES {obj.total_revenue:,.2f}"

    total_revenue.short_description = "Revenue"

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            "pending": "orange",
            "due_soon": "red",
            "overdue": "darkred",
            "remitted": "green",
        }
        color = colors.get(obj.status, "gray")
        text_color = "white" if obj.status in ["due_soon", "overdue"] else "white"
        return format_html(
            f'<span style="color: {text_color}; background-color: {color}; padding: 3px 8px; border-radius: 3px;">{obj.get_status_display()}</span>'
        )

    status_badge.short_description = "Status"

    def days_until_due_display(self, obj):
        """Display days until tax is due with color coding."""
        if obj.status == "remitted":
            return format_html('<span style="color: green;">&#10003; Remitted</span>')

        if obj.due_date:
            today = date.today()
            days = (obj.due_date - today).days

            if days < 0:
                color = "darkred"
                text = f"{abs(days)} days overdue"
            elif days <= 7:
                color = "red"
                text = f"{days} days remaining"
            elif days <= 30:
                color = "orange"
                text = f"{days} days remaining"
            else:
                color = "green"
                text = f"{days} days remaining"

            return format_html(
                f'<span style="color: {color}; font-weight: bold;">{text}</span>'
            )
        return "—"

    days_until_due_display.short_description = "Due Status"
