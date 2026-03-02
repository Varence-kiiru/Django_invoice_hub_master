from django.contrib import admin
from .models import PaymentReceiptNumberSequence, PaymentMethod, Payment, PaymentReconciliation


@admin.register(PaymentReceiptNumberSequence)
class PaymentReceiptNumberSequenceAdmin(admin.ModelAdmin):
    """Admin for payment receipt number sequences."""
    list_display = ('prefix', 'year', 'next_sequence', 'created_at')
    list_filter = ('prefix', 'year')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Sequence Information', {
            'fields': ('prefix', 'year', 'next_sequence')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of number sequences."""
        return False


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'amount', 'payment_method', 'payment_date', 'status')
    list_filter = ('status', 'payment_method', 'payment_date')
    search_fields = ('invoice__invoice_number', 'transaction_reference')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Payment Details', {
            'fields': ('invoice', 'amount', 'payment_method', 'payment_date')
        }),
        ('Status & Reference', {
            'fields': ('status', 'transaction_reference', 'recorded_by')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at', 'notes'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentReconciliation)
class PaymentReconciliationAdmin(admin.ModelAdmin):
    list_display = ('payment', 'invoice', 'amount_matched', 'matched_at')
    list_filter = ('matched_at',)
    search_fields = ('payment__invoice__invoice_number', 'invoice__invoice_number')
    readonly_fields = ('created_at',)
