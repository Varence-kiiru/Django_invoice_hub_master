from django.contrib import admin
from .models import TaxRate, VATRule


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'rate_percentage', 'is_vat_applicable', 'effective_from', 'effective_to')
    list_filter = ('tax_type', 'country', 'is_vat_applicable', 'effective_from')
    search_fields = ('code', 'name')
    readonly_fields = ('created_at', 'is_active')
    fieldsets = (
        ('Basic Info', {
            'fields': ('code', 'name', 'tax_type', 'country')
        }),
        ('Rate Details', {
            'fields': ('rate_percentage', 'is_vat_applicable', 'kra_code')
        }),
        ('Validity', {
            'fields': ('effective_from', 'effective_to')
        }),
        ('Additional', {
            'fields': ('description', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(VATRule)
class VATRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'tax_class', 'tax_rate', 'priority', 'is_active')
    list_filter = ('tax_class', 'is_active', 'priority')
    search_fields = ('name',)
    readonly_fields = ('created_at',)
