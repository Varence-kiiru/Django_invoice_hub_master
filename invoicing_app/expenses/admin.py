"""Django admin interface for expenses app."""

from django.contrib import admin
from django.utils.html import format_html
from .models import ExpenseCategory, Vendor, Expense, ExpenseBudget


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    """Admin for expense categories."""

    list_display = ["name", "is_active", "created_at"]
    search_fields = ["name"]
    list_filter = ["is_active", "created_at"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    """Admin for vendors."""

    list_display = ["name", "contact_email", "contact_phone", "is_active"]
    search_fields = ["name", "contact_email"]
    list_filter = ["is_active", "created_at"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "contact_email", "contact_phone", "address")},
        ),
        ("Payment", {"fields": ("payment_terms",)}),
        ("Status", {"fields": ("is_active",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    """Admin for expenses."""

    list_display = [
        "description_short",
        "get_amount",
        "category",
        "vendor",
        "expense_date",
        "status_badge",
    ]
    search_fields = ["description", "reference_number", "vendor__name"]
    list_filter = ["status", "category", "expense_date", "payment_method"]
    readonly_fields = [
        "created_at",
        "updated_at",
        "submitted_date",
        "approved_date",
        "paid_date",
    ]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("description", "category", "vendor", "notes")},
        ),
        ("Amount & Currency", {"fields": ("amount", "currency")}),
        (
            "Dates",
            {
                "fields": (
                    "expense_date",
                    "submitted_date",
                    "approved_date",
                    "paid_date",
                )
            },
        ),
        (
            "Payment Details",
            {"fields": ("payment_method", "reference_number", "receipt_file")},
        ),
        ("Status & Approval", {"fields": ("status", "submitted_by", "approved_by")}),
        (
            "Reimbursement",
            {
                "fields": ("is_reimbursable", "reimbursed_to", "reimbursement_amount"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def description_short(self, obj):
        """Short description in admin list."""
        return obj.description[:50] if len(obj.description) > 50 else obj.description

    description_short.short_description = "Description"

    def get_amount(self, obj):
        """Display expense amount."""
        return obj.get_display_amount()

    get_amount.short_description = "Amount"

    def status_badge(self, obj):
        """Status with color badge."""
        colors = {
            "draft": "#6c757d",
            "submitted": "#0dcaf0",
            "approved": "#198754",
            "rejected": "#dc3545",
            "paid": "#0d6efd",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"


@admin.register(ExpenseBudget)
class ExpenseBudgetAdmin(admin.ModelAdmin):
    """Admin for expense budgets."""

    list_display = [
        "category",
        "monthly_limit",
        "get_spent",
        "get_remaining",
        "budget_status",
    ]
    list_filter = ["category"]
    readonly_fields = ["created_at", "updated_at"]

    def get_spent(self, obj):
        """Display spent amount."""
        from django.utils.html import format_html

        spent = obj.get_monthly_spent()
        return format_html("${:,.2f}", spent)

    get_spent.short_description = "Monthly Spent"

    def get_remaining(self, obj):
        """Display remaining budget."""
        from django.utils.html import format_html

        spent = obj.get_monthly_spent()
        remaining = obj.monthly_limit - spent
        color = "red" if remaining < 0 else "green"
        return format_html('<span style="color: {};">${:,.2f}</span>', color, remaining)

    get_remaining.short_description = "Remaining"

    def budget_status(self, obj):
        """Display budget status with indicator."""
        from django.utils.html import format_html

        if obj.is_over_budget():
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ OVER BUDGET</span>'
            )
        elif obj.is_alert_threshold_reached():
            return format_html(
                '<span style="color: orange; font-weight: bold;">⚡ Alert Threshold</span>'
            )
        return format_html('<span style="color: green;">✓ On Track</span>')

    budget_status.short_description = "Budget Status"
