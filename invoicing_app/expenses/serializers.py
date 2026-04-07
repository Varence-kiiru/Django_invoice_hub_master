"""Serializers for expenses API."""

from rest_framework import serializers
from .models import Expense, ExpenseCategory, Vendor


class ExpenseCategorySerializer(serializers.ModelSerializer):
    """Serializer for expense categories."""

    class Meta:
        model = ExpenseCategory
        fields = ["id", "name", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class VendorSerializer(serializers.ModelSerializer):
    """Serializer for vendors."""

    class Meta:
        model = Vendor
        fields = [
            "id",
            "name",
            "contact_email",
            "contact_phone",
            "address",
            "payment_terms",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ExpenseSerializer(serializers.ModelSerializer):
    """Serializer for expenses."""

    category_name = serializers.CharField(source="category.name", read_only=True)
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    display_amount = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = [
            "id",
            "description",
            "category",
            "category_name",
            "vendor",
            "vendor_name",
            "amount",
            "currency",
            "display_amount",
            "expense_date",
            "status",
            "payment_method",
            "reference_number",
            "notes",
            "receipt_file",
            "is_reimbursable",
            "reimbursed_to",
            "reimbursement_amount",
            "approved_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_display_amount(self, obj):
        """Get formatted amount display."""
        return obj.get_display_amount()
