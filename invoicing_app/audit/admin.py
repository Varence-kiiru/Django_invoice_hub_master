from django.contrib import admin
from .models import InvoiceSnapshot, AuditLog, LoginHistory


@admin.register(InvoiceSnapshot)
class InvoiceSnapshotAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'snapshot_version', 'snapshot_date', 'is_kra_verified')
    list_filter = ('snapshot_date', 'is_kra_verified')
    search_fields = ('invoice_number',)
    readonly_fields = ('invoice', 'invoice_number', 'snapshot_date', 'invoice_state_json', 'created_at')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('entity_type', 'entity_id', 'action', 'actor', 'timestamp', 'is_kra_verified')
    list_filter = ('entity_type', 'action', 'timestamp', 'is_kra_verified')
    search_fields = ('entity_type', 'actor__email')
    readonly_fields = ('entity_type', 'entity_id', 'action', 'actor', 'timestamp', 'old_values', 'new_values', 'ip_address', 'user_agent')


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    """Admin interface for login history audit trail."""
    list_display = ('user', 'login_time', 'logout_time', 'ip_address', 'device_info', 'is_successful')
    list_filter = ('is_successful', 'login_time', 'device_info')
    search_fields = ('user__username', 'user__email', 'ip_address', 'location')
    readonly_fields = ('user', 'login_time', 'logout_time', 'ip_address', 'user_agent', 'device_info', 'location', 'session_id', 'is_successful')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'is_successful')
        }),
        ('Timing', {
            'fields': ('login_time', 'logout_time')
        }),
        ('Security & Location', {
            'fields': ('ip_address', 'device_info', 'location')
        }),
        ('Technical Details', {
            'fields': ('user_agent', 'session_id'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """LoginHistory is audit-only, no manual creation."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """LoginHistory is immutable audit log."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """LoginHistory is read-only."""
        return False

