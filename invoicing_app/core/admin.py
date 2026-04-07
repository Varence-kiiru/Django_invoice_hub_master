"""Django admin configuration for core app."""

from django.contrib import admin
from invoicing_app.core.models import (
    Backup,
    FAQ,
    HelpArticle,
    SupportTicket,
    CompanySettings,
    EmailConfiguration,
    SavedFilter,
)


@admin.register(Backup)
class BackupAdmin(admin.ModelAdmin):
    """Backup admin configuration - read-only audit trail."""

    list_display = (
        "file_name",
        "backup_type",
        "status",
        "file_size",
        "created_at",
        "created_by_name",
    )
    list_filter = ("backup_type", "status", "is_automated", "created_at")
    search_fields = ("file_name", "file_path", "created_by__username")
    ordering = ["-created_at"]

    fieldsets = (
        (
            "Backup Information",
            {"fields": ("file_name", "file_path", "backup_type", "status")},
        ),
        ("File Details", {"fields": ("file_size", "is_compressed", "checksum")}),
        ("Backup Duration", {"fields": ("duration_seconds",)}),
        ("Creation", {"fields": ("created_by", "is_automated", "created_at")}),
        (
            "Restoration",
            {"fields": ("restored_at", "restored_by"), "classes": ("collapse",)},
        ),
        ("Additional", {"fields": ("notes",), "classes": ("collapse",)}),
    )
    readonly_fields = (
        "file_name",
        "file_path",
        "file_size",
        "backup_type",
        "status",
        "checksum",
        "created_by",
        "created_at",
        "restored_at",
        "restored_by",
        "is_compressed",
        "is_automated",
        "notes",
        "duration_seconds",
    )

    def created_by_name(self, obj):
        """Display created by user, or 'System' if automated."""
        if obj.is_automated:
            return "System (Automated)"
        return obj.created_by.username if obj.created_by else "Unknown"

    created_by_name.short_description = "Created By"

    def has_add_permission(self, request):
        """Backups are created by system only."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Backups are immutable audit trail."""
        return False

    def has_change_permission(self, request, obj=None):
        """Backups are read-only."""
        return False


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """FAQ admin configuration."""

    list_display = (
        "question",
        "category",
        "is_active",
        "views_count",
        "helpful_yes",
        "created_at",
    )
    list_filter = ("category", "is_active", "created_at")
    search_fields = ("question", "answer")
    ordering = ["category", "order", "-created_at"]
    fieldsets = (
        ("Question & Answer", {"fields": ("category", "question", "answer", "order")}),
        (
            "Metrics",
            {
                "fields": ("views_count", "helpful_yes", "helpful_no"),
                "classes": ("collapse",),
            },
        ),
        ("Status", {"fields": ("is_active",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "views_count",
        "helpful_yes",
        "helpful_no",
    )


@admin.register(HelpArticle)
class HelpArticleAdmin(admin.ModelAdmin):
    """Help article admin configuration."""

    list_display = (
        "title",
        "category",
        "featured",
        "is_active",
        "views_count",
        "created_at",
    )
    list_filter = ("category", "featured", "is_active", "created_at")
    search_fields = ("title", "excerpt", "tags")
    slugify_fields = ("slug",)
    ordering = ["-featured", "category", "order", "-created_at"]

    fieldsets = (
        (
            "Article Information",
            {"fields": ("title", "slug", "category", "excerpt", "author")},
        ),
        ("Content", {"fields": ("content", "tags")}),
        ("Display", {"fields": ("featured", "order")}),
        ("Metrics", {"fields": ("views_count",), "classes": ("collapse",)}),
        ("Status", {"fields": ("is_active",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ("created_at", "updated_at", "views_count")


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    """Support ticket admin configuration."""

    list_display = (
        "ticket_number",
        "name",
        "subject",
        "status",
        "priority",
        "created_at",
    )
    list_filter = ("status", "priority", "category", "created_at")
    search_fields = ("ticket_number", "name", "email", "subject", "message")
    ordering = ["-created_at"]

    fieldsets = (
        (
            "Ticket Information",
            {"fields": ("ticket_number", "name", "email", "subject")},
        ),
        ("Details", {"fields": ("category", "priority", "message")}),
        ("Assignment & Status", {"fields": ("assigned_to", "status", "resolved_at")}),
        ("Resolution", {"fields": ("resolution_notes",), "classes": ("collapse",)}),
        ("Attachment", {"fields": ("attachment_url",), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ("ticket_number", "created_at", "updated_at")

    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly for regular staff."""
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing
            if not request.user.is_superuser:
                readonly.extend(
                    ["ticket_number", "name", "email", "subject", "message"]
                )
        return readonly


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    """Company settings admin configuration."""

    list_display = ("company_name", "updated_at")

    fieldsets = (
        (
            "Company Information",
            {
                "fields": (
                    "company_name",
                    "company_email",
                    "company_phone",
                    "company_website",
                )
            },
        ),
        (
            "Address",
            {"fields": ("street_address", "city", "state", "postal_code", "country")},
        ),
        (
            "Financial Settings",
            {
                "fields": (
                    "default_currency",
                    "tax_id",
                    "registration_number",
                    "bank_account_info",
                )
            },
        ),
        (
            "Invoice Settings",
            {
                "fields": (
                    "invoice_prefix",
                    "invoice_start_number",
                    "invoice_due_days",
                    "invoice_notes",
                )
            },
        ),
        (
            "Payment Settings",
            {"fields": ("accepted_payment_methods", "payment_instructions")},
        ),
        ("Terms & Conditions", {"fields": ("terms_and_conditions",)}),
        ("Support Settings", {"fields": ("support_email",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(EmailConfiguration)
class EmailConfigurationAdmin(admin.ModelAdmin):
    """Email configuration admin."""

    list_display = ("is_configured", "last_tested_at", "last_test_status")
    list_filter = ("is_configured", "last_test_status")

    fieldsets = (
        ("Email Provider", {"fields": ("email_provider",)}),
        (
            "Configuration",
            {
                "fields": (
                    "smtp_host",
                    "smtp_port",
                    "smtp_username",
                    "smtp_password",
                    "from_name",
                    "from_email",
                )
            },
        ),
        ("Status", {"fields": ("is_configured",)}),
        (
            "Test Results",
            {
                "fields": ("last_tested_at", "last_test_status", "last_test_error"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = (
        "last_tested_at",
        "last_test_status",
        "last_test_error",
        "created_at",
        "updated_at",
    )


@admin.register(SavedFilter)
class SavedFilterAdmin(admin.ModelAdmin):
    """Saved filter presets admin configuration."""

    list_display = (
        "name",
        "filter_type",
        "created_by",
        "is_global",
        "use_count",
        "last_used",
        "created_at",
    )
    list_filter = ("filter_type", "is_global", "created_at")
    search_fields = ("name", "description", "created_by__username")
    ordering = ["-last_used", "-created_at"]

    fieldsets = (
        ("Filter Information", {"fields": ("name", "description", "filter_type")}),
        (
            "Filter Criteria",
            {
                "fields": ("filter_criteria",),
                "description": 'Define filter conditions as JSON (e.g., {"status": "unpaid", "days_overdue": {"gte": 30}})',
            },
        ),
        ("Sorting & Display", {"fields": ("sort_by",), "classes": ("collapse",)}),
        ("Ownership & Sharing", {"fields": ("created_by", "is_global")}),
        ("Usage", {"fields": ("last_used", "use_count"), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ("last_used", "use_count", "created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        """Auto-set created_by on creation."""
        if not change:  # Creating new
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
