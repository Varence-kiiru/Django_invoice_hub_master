from rest_framework import serializers
import re
from invoicing_app.products.models import Product, ProductCategory, ProductTaxClass
from invoicing_app.core.validators import ProductValidationMixin, ValidationMixin


class ProductCategorySerializer(serializers.ModelSerializer):
    """
    Product category serializer.
    """

    class Meta:
        model = ProductCategory
        fields = [
            "id",
            "uuid",
            "name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "uuid", "created_at", "updated_at"]


class ProductTaxClassSerializer(serializers.ModelSerializer):
    """
    Product tax class serializer.
    Maps products to VAT treatment (Standard, Zero-rated, Exempt).
    """

    class Meta:
        model = ProductTaxClass
        fields = ["id", "name", "rate_type", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProductSerializer(
    ProductValidationMixin, ValidationMixin, serializers.ModelSerializer
):
    """
    Product/service serializer with category and tax class support.
    Includes comprehensive validation for SKU, pricing, and category.
    """

    category = ProductCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductCategory.objects.all(),
        source="category",
        write_only=True,
        required=False,
    )
    tax_class = ProductTaxClassSerializer(read_only=True)
    tax_class_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductTaxClass.objects.all(), source="tax_class", write_only=True
    )
    created_by_email = serializers.CharField(
        source="created_by.email", read_only=True, allow_null=True
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "uuid",
            "sku",
            "name",
            "description",
            "category",
            "category_id",
            "tax_class",
            "tax_class_id",
            "unit_price",
            "unit",
            "is_active",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "uuid", "created_at", "updated_at"]

    def validate_sku(self, value):
        """
        Validate SKU format (alphanumeric with hyphens and underscores).
        """
        if not value:
            raise serializers.ValidationError("SKU is required.")

        if len(value) < 2:
            raise serializers.ValidationError("SKU must be at least 2 characters long.")

        if len(value) > 50:
            raise serializers.ValidationError("SKU cannot exceed 50 characters.")

        # Allow alphanumeric, hyphens, underscores
        if not re.match(r"^[a-zA-Z0-9_-]+$", value):
            raise serializers.ValidationError(
                "SKU can only contain alphanumeric characters, hyphens, and underscores."
            )

        # Check uniqueness (excluding current product in update)
        queryset = Product.objects.filter(sku__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("SKU must be unique.")

        return value.upper()

    def validate_unit_price(self, value):
        """
        Validate unit price is positive.
        """
        if value is not None:
            self.validate_positive_decimal(value, "Unit price")
        return value

    def validate_category_id(self, value):
        """
        Validate category exists and is active.
        """
        if value and not value.is_active:
            raise serializers.ValidationError(
                "Selected category is inactive. Please choose an active category."
            )
        return value
