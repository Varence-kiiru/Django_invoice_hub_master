"""Admin configuration for Deliveries app."""

from django.contrib import admin
from invoicing_app.deliveries.models import (
    Delivery,
    DeliveryLineItem,
    DeliveryNumberSequence,
)


class DeliveryLineItemInline(admin.TabularInline):
    """Inline admin for delivery line items."""

    model = DeliveryLineItem
    extra = 0
    fields = ("product", "quantity_scheduled", "quantity_delivered", "unit", "notes")
    readonly_fields = ("product",)


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    """Admin interface for deliveries."""

    list_display = (
        "delivery_number",
        "invoice",
        "status",
        "scheduled_date",
        "actual_delivery_date",
        "delivery_method",
    )
    list_filter = (
        "status",
        "delivery_method",
        "scheduled_date",
        "actual_delivery_date",
    )
    search_fields = ("delivery_number", "invoice__invoice_number", "tracking_number")
    readonly_fields = (
        "delivery_number",
        "created_at",
        "updated_at",
        "created_by",
        "total_items_scheduled",
        "total_items_delivered",
    )
    fieldsets = (
        ("Identification", {"fields": ("delivery_number", "invoice", "created_by")}),
        (
            "Delivery Schedule",
            {"fields": ("scheduled_date", "actual_delivery_date", "delivery_time")},
        ),
        (
            "Status & Tracking",
            {"fields": ("status", "tracking_number", "delivery_method")},
        ),
        (
            "Delivery Details",
            {
                "fields": (
                    "delivery_location",
                    "recipient_name",
                    "condition",
                    "condition_notes",
                )
            },
        ),
        (
            "Items",
            {
                "fields": ("total_items_scheduled", "total_items_delivered"),
                "description": "Summary of items in this delivery",
            },
        ),
        (
            "Additional Info",
            {"fields": ("notes", "delivery_pdf"), "classes": ("collapse",)},
        ),
        (
            "Metadata",
            {
                "fields": ("created_at", "updated_at", "is_active"),
                "classes": ("collapse",),
            },
        ),
    )
    inlines = [DeliveryLineItemInline]
    date_hierarchy = "scheduled_date"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DeliveryNumberSequence)
class DeliveryNumberSequenceAdmin(admin.ModelAdmin):
    """Admin interface for delivery number sequences."""

    list_display = ("prefix", "year", "next_sequence", "created_at")
    list_filter = ("prefix", "year")
    readonly_fields = ("created_at",)
    fieldsets = (
        ("Configuration", {"fields": ("prefix", "year")}),
        ("Sequence", {"fields": ("next_sequence",)}),
        ("Metadata", {"fields": ("created_at",), "classes": ("collapse",)}),
    )
