"""
Management command to fix unicode escape sequences in database fields.

This command finds and replaces unicode escape sequences like \\u0026 (ampersand)
that were accidentally stored as literal text instead of being decoded.

Run with: python manage.py fix_unicode_escapes
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Fix unicode escape sequences in text fields."""

    help = "Replace unicode escape sequences (e.g., \\u0026) with actual characters in database fields"

    # Common unicode escapes that need fixing
    # These are literal strings with backslash-u sequences
    UNICODE_ESCAPES = [
        ("\\u0026", "&"),  # Ampersand
        ("\\u003c", "<"),  # Less than
        ("\\u003e", ">"),  # Greater than
        ("\\u0027", "'"),  # Single quote
        ("\\u0022", '"'),  # Double quote
        ("\\u005c", "\\"),  # Backslash
        ("\\u002f", "/"),  # Forward slash
    ]

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without making changes",
        )
        parser.add_argument(
            "--model",
            type=str,
            help='Only fix specific model (e.g., "products.Product" or "quotations.QuoteLineItem")',
        )

    def handle(self, *args, **options):
        """Execute the command."""
        dry_run = options.get("dry_run", False)
        model_filter = options.get("model")

        self.stdout.write(self.style.SUCCESS("\n" + "=" * 70))
        self.stdout.write(self.style.SUCCESS("Unicode Escape Sequence Fixer"))
        self.stdout.write(self.style.SUCCESS("=" * 70 + "\n"))

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made\n")
            )

        # Import all models
        from invoicing_app.quotations.models import Quote, QuoteLineItem
        from invoicing_app.invoices.models import Invoice, InvoiceLineItem
        from invoicing_app.products.models import Product
        from invoicing_app.clients.models import Client

        models_to_fix = [
            ("QuoteLineItem", QuoteLineItem, ["description", "notes"]),
            ("InvoiceLineItem", InvoiceLineItem, ["description", "notes"]),
            ("Product", Product, ["name", "description", "sku"]),
            ("Quote", Quote, ["description"]),
            ("Invoice", Invoice, ["description"]),
            ("Client", Client, ["name"]),
        ]

        # Filter by model if specified
        if model_filter:
            models_to_fix = [
                m for m in models_to_fix if model_filter.lower() in m[0].lower()
            ]

        total_fixed = 0

        for model_name, model_class, fields in models_to_fix:
            self.stdout.write(self.style.HTTP_INFO(f"\nProcessing {model_name}..."))

            for field_name in fields:
                fixed_count = self._fix_field(model_class, field_name, dry_run)
                total_fixed += fixed_count

                if fixed_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ {field_name}: Fixed {fixed_count} records"
                        )
                    )

        self.stdout.write("\n" + "=" * 70)
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"DRY RUN: Would fix {total_fixed} total fields")
            )
        else:
            self.stdout.write(self.style.SUCCESS(f"✓ Fixed {total_fixed} total fields"))
        self.stdout.write("=" * 70 + "\n")

    def _fix_field(self, model_class, field_name, dry_run):
        """Fix unicode escapes in a specific field of a model."""
        fixed_count = 0

        # Get all records with any of the unicode escape patterns
        records = model_class.objects.all()

        for record in records:
            field_value = getattr(record, field_name, "")

            if not isinstance(field_value, str):
                continue

            original_value = field_value

            # Apply all replacements using simple string replacement
            for escape_seq, replacement in self.UNICODE_ESCAPES:
                field_value = field_value.replace(escape_seq, replacement)

            # If value changed, update it
            if field_value != original_value:
                if not dry_run:
                    setattr(record, field_name, field_value)
                    record.save(update_fields=[field_name])

                self.stdout.write(
                    f"    {model_class.__name__}(id={record.id}).{field_name}"
                )
                self.stdout.write(f"      Before: {original_value[:60]}...")
                self.stdout.write(f"      After:  {field_value[:60]}...")

                fixed_count += 1

        return fixed_count
