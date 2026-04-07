from django.contrib import admin
from .models import Client, ClientAddress, ClientContact


class ClientAddressInline(admin.TabularInline):
    model = ClientAddress
    extra = 1
    fields = ("address_type", "street_1", "city", "country", "is_primary")


class ClientContactInline(admin.TabularInline):
    model = ClientContact
    extra = 1
    fields = ("name", "title", "email", "phone", "is_primary")


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "client_type", "email", "tax_id", "currency", "is_active")
    list_filter = ("client_type", "currency", "is_active", "created_at")
    search_fields = ("name", "email", "tax_id")
    readonly_fields = ("uuid", "created_at", "updated_at")
    inlines = [ClientAddressInline, ClientContactInline]
    fieldsets = (
        ("Basic Info", {"fields": ("name", "uuid", "client_type", "email", "phone")}),
        ("Tax & Registration", {"fields": ("tax_id", "business_registration_number")}),
        (
            "Billing",
            {
                "fields": (
                    "currency",
                    "default_tax_rate",
                    "payment_terms_days",
                    "credit_limit",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "is_active",
                    "created_by",
                    "created_at",
                    "updated_at",
                    "notes",
                ),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ClientAddress)
class ClientAddressAdmin(admin.ModelAdmin):
    list_display = ("client", "address_type", "city", "is_primary")
    list_filter = ("address_type", "is_primary")
    search_fields = ("client__name", "city")


@admin.register(ClientContact)
class ClientContactAdmin(admin.ModelAdmin):
    list_display = ("name", "client", "title", "email", "is_primary")
    list_filter = ("is_primary",)
    search_fields = ("name", "email", "client__name")
