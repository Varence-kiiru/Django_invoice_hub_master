from django.contrib import admin
from django.utils.html import format_html
from .models import Organization, OrganizationMember, Subscription, Invoice


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "plan_badge",
        "status_badge",
        "user_count",
        "invoice_count",
        "admin_email",
        "subscription_started",
    ]
    list_filter = ["plan", "status", "created_at"]
    search_fields = ["name", "slug", "admin_email"]
    readonly_fields = [
        "uuid",
        "stripe_customer_id",
        "stripe_subscription_id",
        "api_key",
        "created_at",
        "updated_at",
        "subscription_started",
    ]

    fieldsets = (
        (
            "Organization Info",
            {"fields": ("name", "slug", "description", "website", "logo")},
        ),
        ("Contact", {"fields": ("admin_email", "phone")}),
        (
            "Subscription",
            {
                "fields": (
                    "plan",
                    "status",
                    "subscription_started",
                    "subscription_renew_date",
                )
            },
        ),
        ("Billing", {"fields": ("stripe_customer_id", "stripe_subscription_id")}),
        ("Usage", {"fields": ("user_count", "invoice_count")}),
        (
            "Features",
            {
                "fields": (
                    "enable_api_access",
                    "enable_custom_branding",
                    "enable_advanced_analytics",
                    "enable_api_webhooks",
                )
            },
        ),
        ("API", {"fields": ("api_key",), "classes": ("collapse",)}),
        (
            "System",
            {
                "fields": ("uuid", "created_at", "updated_at", "is_active"),
                "classes": ("collapse",),
            },
        ),
    )

    def plan_badge(self, obj):
        colors = {
            "free": "#gray",
            "starter": "#0099ff",
            "professional": "#00cc00",
            "enterprise": "#ff6600",
        }
        return format_html(
            '<span style="padding: 3px 10px; background-color: {}; color: white; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.plan, "#gray"),
            obj.get_plan_display(),
        )

    plan_badge.short_description = "Plan"

    def status_badge(self, obj):
        colors = {
            "active": "#00cc00",
            "suspended": "#ff6600",
            "cancelled": "#cc0000",
            "trial": "#0099ff",
        }
        return format_html(
            '<span style="padding: 3px 10px; background-color: {}; color: white; border-radius: 3px;">{}</span>',
            colors.get(obj.status, "#gray"),
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ["user", "organization", "role", "is_primary", "joined_at"]
    list_filter = ["organization", "role", "is_primary"]
    search_fields = ["user__email", "organization__name"]
    readonly_fields = ["created_at", "updated_at", "joined_at"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "organization",
        "plan",
        "status_badge",
        "amount",
        "current_period_end",
        "auto_renew",
    ]
    list_filter = ["plan", "status", "payment_method"]
    search_fields = ["organization__name"]
    readonly_fields = ["created_at", "updated_at", "start_date"]

    def status_badge(self, obj):
        colors = {
            "active": "#00cc00",
            "expired": "#cc0000",
            "cancelled": "#999999",
            "past_due": "#ff6600",
            "trialing": "#0099ff",
        }
        return format_html(
            '<span style="padding: 3px 10px; background-color: {}; color: white; border-radius: 3px;">{}</span>',
            colors.get(obj.status, "#gray"),
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"


@admin.register(Invoice)
class BillingInvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "invoice_number",
        "organization",
        "amount",
        "status_badge",
        "due_date",
        "issue_date",
    ]
    list_filter = ["status", "issue_date"]
    search_fields = ["invoice_number", "organization__name"]
    readonly_fields = ["uuid", "created_at", "updated_at", "issue_date"]

    def status_badge(self, obj):
        colors = {
            "draft": "#999999",
            "issued": "#0099ff",
            "paid": "#00cc00",
            "failed": "#cc0000",
            "refunded": "#ff6600",
        }
        return format_html(
            '<span style="padding: 3px 10px; background-color: {}; color: white; border-radius: 3px;">{}</span>',
            colors.get(obj.status, "#gray"),
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"
