"""
Django admin configuration for Quotations.
"""

from django.contrib import admin
from .models import Quote, QuoteLineItem, QuoteNumberSequence


class QuoteLineItemInline(admin.TabularInline):
    """Inline admin for quote line items."""

    model = QuoteLineItem
    extra = 0
    fields = [
        "product",
        "description",
        "quantity",
        "unit_price",
        "tax_rate",
        "line_total",
    ]
    readonly_fields = ["line_total"]


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    """Admin interface for quotes."""

    list_display = [
        "quote_number",
        "client",
        "quote_date",
        "total_amount",
        "status",
        "valid_until",
    ]
    list_filter = ["status", "quote_date", "currency", "created_at"]
    search_fields = ["quote_number", "client__name", "description"]
    readonly_fields = [
        "quote_number",
        "created_at",
        "updated_at",
        "sent_at",
        "viewed_at",
        "accepted_at",
        "rejected_at",
        "expired_at",
        "converted_at",
    ]
    inlines = [QuoteLineItemInline]

    fieldsets = (
        ("Identity", {"fields": ("quote_number",)}),
        ("Client & Dates", {"fields": ("client", "quote_date", "valid_until")}),
        ("Content", {"fields": ("description", "currency")}),
        (
            "Totals",
            {
                "fields": ("subtotal_amount", "vat_amount", "total_amount"),
                "classes": ("wide",),
            },
        ),
        ("Status", {"fields": ("status",)}),
        (
            "Timestamps",
            {
                "fields": (
                    "sent_at",
                    "viewed_at",
                    "accepted_at",
                    "rejected_at",
                    "expired_at",
                    "converted_at",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Conversion",
            {
                "fields": ("converted_invoice", "rejection_reason"),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_by", "updated_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(QuoteNumberSequence)
class QuoteNumberSequenceAdmin(admin.ModelAdmin):
    """Admin interface for quote number sequences."""

    list_display = ["prefix", "year", "next_sequence", "created_at"]
    list_filter = ["prefix", "year"]
    readonly_fields = ["created_at"]
