from django.contrib import admin
from .models import ProductCategory, ProductTaxClass, Product


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    readonly_fields = ('uuid', 'created_at', 'updated_at')


@admin.register(ProductTaxClass)
class ProductTaxClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'rate_type', 'created_at')
    list_filter = ('rate_type',)
    search_fields = ('name',)
    readonly_fields = ('created_at',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'category', 'tax_class', 'unit_price', 'is_active')
    list_filter = ('tax_class', 'category', 'is_active', 'unit')
    search_fields = ('sku', 'name')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Info', {
            'fields': ('uuid', 'sku', 'name', 'category', 'unit')
        }),
        ('Pricing & Tax', {
            'fields': ('unit_price', 'tax_class')
        }),
        ('Audit', {
            'fields': ('is_active', 'created_by', 'created_at', 'updated_at', 'description'),
            'classes': ('collapse',)
        }),
    )
