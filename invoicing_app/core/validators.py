"""Validation utilities and custom validators for all serializers."""

from rest_framework import serializers
from decimal import Decimal


class ValidationMixin:
    """Mixin providing common validation methods for serializers."""

    @staticmethod
    def validate_positive_decimal(value, field_name="Amount"):
        """Ensure a decimal value is positive."""
        if value is None:
            return value
        if isinstance(value, (int, float)):
            value = Decimal(str(value))
        if value <= 0:
            raise serializers.ValidationError(f"{field_name} must be greater than 0.")
        return value

    @staticmethod
    def validate_date_range(start_date, end_date, start_name="Start", end_name="End"):
        """Ensure start_date <= end_date."""
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                f"{start_name} ({start_date}) cannot be after {end_name} ({end_date})."
            )

    @staticmethod
    def validate_max_length(value, max_len, field_name="Field"):
        """Ensure string doesn't exceed max length."""
        if value and len(str(value)) > max_len:
            raise serializers.ValidationError(
                f"{field_name} cannot exceed {max_len} characters."
            )
        return value

    @staticmethod
    def validate_non_negative_decimal(value, field_name="Amount"):
        """Ensure a decimal value is >= 0."""
        if value is None:
            return value
        if isinstance(value, (int, float)):
            value = Decimal(str(value))
        if value < 0:
            raise serializers.ValidationError(f"{field_name} cannot be negative.")
        return value

    @staticmethod
    def validate_percentage(value, field_name="Percentage"):
        """Ensure value is between 0 and 100."""
        if value is None:
            return value
        if isinstance(value, (int, float)):
            value = Decimal(str(value))
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                f"{field_name} must be between 0 and 100."
            )
        return value


class InvoiceValidationMixin(ValidationMixin):
    """Validation methods specific to invoice operations."""

    def validate_invoice_dates(self, data):
        """Ensure invoice_date <= due_date."""
        invoice_date = data.get("invoice_date") or (
            self.instance.invoice_date if self.instance else None
        )
        due_date = data.get("due_date") or (
            self.instance.due_date if self.instance else None
        )

        if invoice_date and due_date:
            self.validate_date_range(invoice_date, due_date, "Invoice date", "Due date")

    def validate_amounts(self, data):
        """Ensure amounts are positive and consistent."""
        subtotal = data.get("subtotal_amount")
        vat = data.get("vat_amount")
        total = data.get("total_amount")

        if subtotal is not None:
            self.validate_positive_decimal(subtotal, "Subtotal amount")

        if vat is not None:
            self.validate_non_negative_decimal(vat, "VAT amount")

        if total is not None:
            self.validate_positive_decimal(total, "Total amount")

        # Check that amounts add up correctly
        if subtotal is not None and vat is not None and total is not None:
            expected_total = subtotal + vat
            if abs(total - expected_total) > Decimal("0.01"):  # Allow small rounding
                raise serializers.ValidationError(
                    {
                        "total_amount": (
                            f"Total amount ({total}) must equal "
                            f"subtotal ({subtotal}) + VAT ({vat})"
                        )
                    }
                )


class PaymentValidationMixin(ValidationMixin):
    """Validation methods specific to payment operations."""

    def validate_payment_amount(self, data, invoice=None):
        """Ensure payment amount is valid and doesn't exceed invoice total."""
        amount = data.get("amount")

        if amount is None:
            return

        self.validate_positive_decimal(amount, "Payment amount")

        # Get invoice to check against
        if not invoice:
            invoice_id = data.get("invoice_id") or (
                self.instance.invoice_id if self.instance else None
            )
            if invoice_id:
                from invoicing_app.invoices.models import Invoice

                try:
                    invoice = Invoice.objects.get(id=invoice_id)
                except Invoice.DoesNotExist:
                    raise serializers.ValidationError({"invoice": "Invoice not found."})

        if invoice:
            if amount > invoice.total_amount:
                raise serializers.ValidationError(
                    {
                        "amount": (
                            f"Payment amount ({amount}) cannot exceed "
                            f"invoice total ({invoice.total_amount})."
                        )
                    }
                )


class ClientValidationMixin(ValidationMixin):
    """Validation methods specific to client operations."""

    def validate_tax_id_format(self, value):
        """Validate tax ID format (Kenya PIN or VAT number)."""
        if not value:
            return value

        # Kenya PIN format: typically 10 digits
        # VAT format: typically 14 digits
        # Allow both patterns
        if not value.replace("-", "").replace(" ", "").isdigit():
            raise serializers.ValidationError(
                "Tax ID must contain only digits, hyphens, and spaces."
            )

        digit_count = len(value.replace("-", "").replace(" ", ""))
        if digit_count < 8:
            raise serializers.ValidationError("Tax ID must have at least 8 digits.")

        return value

    def validate_currency(self, value):
        """Ensure valid currency code."""
        valid_currencies = ["KES", "USD", "EUR"]
        if value not in valid_currencies:
            raise serializers.ValidationError(
                f"Currency must be one of: {', '.join(valid_currencies)}"
            )
        return value


class ProductValidationMixin(ValidationMixin):
    """Validation methods specific to product operations."""

    def validate_sku(self, value):
        """Validate SKU format."""
        if not value:
            return value

        if len(value) < 2:
            raise serializers.ValidationError("SKU must be at least 2 characters long.")

        if not value.replace("-", "").replace("_", "").isalnum():
            raise serializers.ValidationError(
                "SKU can only contain alphanumeric characters, hyphens, and underscores."
            )

        return value

    def validate_unit_price(self, value):
        """Ensure unit price is positive."""
        return self.validate_positive_decimal(value, "Unit price")


class TaxValidationMixin(ValidationMixin):
    """Validation methods specific to tax operations."""

    def validate_rate_percentage(self, value):
        """Ensure rate percentage is valid."""
        if value is None:
            return value

        if isinstance(value, (int, float)):
            value = Decimal(str(value))

        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Tax rate percentage must be between 0 and 100."
            )

        return value

    def validate_effective_dates(self, data):
        """Ensure effective_from <= effective_to."""
        effective_from = data.get("effective_from")
        effective_to = data.get("effective_to")

        if effective_from and effective_to:
            self.validate_date_range(
                effective_from, effective_to, "Effective from", "Effective to"
            )


class PaginationValidator:
    """Validator for pagination parameters."""

    @staticmethod
    def validate_page_size(page_size):
        """Ensure page size is within acceptable bounds."""
        max_page_size = 1000
        min_page_size = 1

        if page_size < min_page_size:
            raise serializers.ValidationError(
                f"Page size must be at least {min_page_size}."
            )

        if page_size > max_page_size:
            raise serializers.ValidationError(
                f"Page size cannot exceed {max_page_size}."
            )

        return page_size


class UniqueTogetherValidator:
    """Custom unique-together validation."""

    @staticmethod
    def validate_unique_together(queryset, data, fields, instance=None):
        """
        Validate that a combination of fields is unique.

        Args:
            queryset: QuerySet to check against
            data: Data dict from serializer
            fields: Tuple of field names to check
            instance: Current instance (for updates)

        Raises:
            ValidationError if combination is not unique
        """
        filter_kwargs = {}
        all_present = True

        for field in fields:
            if field not in data:
                all_present = False
                break
            filter_kwargs[field] = data[field]

        if not all_present:
            return  # Don't validate if not all fields present

        matching = queryset.filter(**filter_kwargs)

        if instance:
            matching = matching.exclude(pk=instance.pk)

        if matching.exists():
            raise serializers.ValidationError(
                {fields[0]: f"This combination of {', '.join(fields)} already exists."}
            )


class UniqueFieldValidator:
    """Validator for unique fields with custom logic."""

    @staticmethod
    def validate_unique_field(queryset, field_name, value, instance=None):
        """
        Validate that a field value is unique.

        Args:
            queryset: QuerySet to check against
            field_name: Name of field to validate
            value: Value to check
            instance: Current instance (for updates)

        Raises:
            ValidationError if not unique
        """
        if value is None:
            return

        filter_kwargs = {field_name: value}
        matching = queryset.filter(**filter_kwargs)

        if instance:
            matching = matching.exclude(pk=instance.pk)

        if matching.exists():
            raise serializers.ValidationError(
                {field_name: f"An object with this {field_name} already exists."}
            )


class NestedValidationMixin:
    """Mixin for validating nested objects."""

    def validate_nested_objects(self, data, nested_field, validator_func):
        """
        Validate nested objects in a serializer.

        Args:
            data: Serializer data
            nested_field: Name of nested field (e.g., 'line_items')
            validator_func: Function that validates each nested object

        Raises:
            ValidationError if any nested object is invalid
        """
        if nested_field not in data:
            return

        nested_objects = data[nested_field]
        if not nested_objects:
            return

        errors = []
        for idx, obj in enumerate(nested_objects):
            try:
                validator_func(obj)
            except serializers.ValidationError as e:
                errors.append(
                    {
                        "line": idx + 1,
                        "errors": e.detail if hasattr(e, "detail") else str(e),
                    }
                )

        if errors:
            raise serializers.ValidationError({nested_field: errors})
