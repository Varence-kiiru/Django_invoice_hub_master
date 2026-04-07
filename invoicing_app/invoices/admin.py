from django.contrib import admin
from .models import InvoiceNumberSequence, Invoice, InvoiceLineItem


class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 1
    fields = (
        "product",
        "description",
        "quantity",
        "unit_price",
        "tax_rate",
        "tax_amount",
        "line_total",
    )
    readonly_fields = ("line_total",)


@admin.register(InvoiceNumberSequence)
class InvoiceNumberSequenceAdmin(admin.ModelAdmin):
    list_display = ("prefix", "year", "next_sequence")
    list_filter = ("prefix", "year")
    readonly_fields = ("created_at",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "client",
        "invoice_date",
        "due_date",
        "total_amount",
        "status",
    )
    list_filter = ("status", "currency", "invoice_date", "is_active")
    search_fields = ("invoice_number", "client__name")
    readonly_fields = (
        "uuid",
        "invoice_number",
        "subtotal_amount",
        "vat_amount",
        "total_amount",
        "amount_due",
        "created_at",
        "updated_at",
    )
    inlines = [InvoiceLineItemInline]
    fieldsets = (
        (
            "Invoice Details",
            {"fields": ("uuid", "invoice_number", "client", "status", "currency")},
        ),
        ("Dates", {"fields": ("invoice_date", "due_date")}),
        (
            "Totals",
            {
                "fields": (
                    "subtotal_amount",
                    "vat_amount",
                    "total_amount",
                    "amount_paid",
                    "amount_due",
                )
            },
        ),
        (
            "Activity Timeline",
            {
                "fields": (
                    "issued_at",
                    "sent_at",
                    "viewed_at",
                    "first_reminder_sent_at",
                    "second_reminder_sent_at",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Cancellation",
            {
                "fields": ("cancelled_at", "cancellation_reason"),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "is_active",
                    "created_by",
                    "updated_by",
                    "created_at",
                    "updated_at",
                    "description",
                ),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(InvoiceLineItem)
class InvoiceLineItemAdmin(admin.ModelAdmin):
    list_display = ("invoice", "description", "quantity", "unit_price", "line_total")
    list_filter = ("invoice__status", "tax_rate")
    search_fields = ("invoice__invoice_number", "description")
    readonly_fields = ("created_at", "updated_at")
