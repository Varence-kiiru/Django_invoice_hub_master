from django.contrib import admin
from .models import EmailTemplate, NotificationLog


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("notification_type", "recipient", "status", "created_at")
    list_filter = ("notification_type", "status", "created_at")
    search_fields = ("recipient", "entity_type")
    readonly_fields = ("created_at",)
