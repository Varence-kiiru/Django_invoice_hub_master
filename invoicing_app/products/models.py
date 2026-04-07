"""
Products/services catalog models.
"""

from django.db import models
from invoicing_app.core.models import ActiveModel


class ProductCategory(ActiveModel):
    """
    Product category for organization and filtering.
    """

    name = models.CharField(
        max_length=100, unique=True, db_index=True, help_text="Category name (unique)"
    )
    description = models.TextField(
        blank=True, null=True, help_text="Description of this category"
    )

    class Meta:
        db_table = "products_productcategory"
        ordering = ["name"]
        verbose_name_plural = "Product Categories"
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name


class ProductTaxClass(ActiveModel):
    """
    Tax classification for products (determines default VAT treatment).
    """

    RATE_TYPE_CHOICES = [
        ("standard", "Standard VAT (16%)"),
        ("zero", "Zero-Rated (0%)"),
        ("exempt", "Exempt (no VAT)"),
    ]

    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Tax class name (e.g., 'Standard VAT', 'Zero-Rated')",
    )
    rate_type = models.CharField(
        max_length=20, choices=RATE_TYPE_CHOICES, help_text="Type of VAT treatment"
    )

    class Meta:
        db_table = "products_producttaxclass"
        ordering = ["name"]
        verbose_name_plural = "Product Tax Classes"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["rate_type"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_rate_type_display()})"


class Product(ActiveModel):
    """
    Product or service in the catalog.
    """

    UNIT_CHOICES = [
        ("piece", "Piece"),
        ("kg", "Kilogram"),
        ("liter", "Liter"),
        ("meter", "Meter"),
        ("hour", "Hour"),
        ("day", "Day"),
        ("service", "Service"),
        ("other", "Other"),
    ]

    sku = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Stock keeping unit (unique)",
    )
    name = models.CharField(
        max_length=255, db_index=True, help_text="Product/service name"
    )
    description = models.TextField(
        blank=True, null=True, help_text="Detailed description"
    )
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        help_text="Product category",
    )
    tax_class = models.ForeignKey(
        ProductTaxClass,
        on_delete=models.PROTECT,
        related_name="products",
        help_text="Default VAT treatment for this product",
    )
    unit_price = models.DecimalField(
        max_digits=15, decimal_places=2, help_text="Base price (excluding VAT)"
    )
    unit = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        default="piece",
        help_text="Unit of measurement",
    )
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_products",
        help_text="User who created this product",
    )

    class Meta:
        db_table = "products_product"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["name"]),
            models.Index(fields=["category"]),
            models.Index(fields=["tax_class"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def clean(self):
        """Validate unit_price > 0."""
        from django.core.exceptions import ValidationError

        if self.unit_price <= 0:
            raise ValidationError("Unit price must be greater than 0")
