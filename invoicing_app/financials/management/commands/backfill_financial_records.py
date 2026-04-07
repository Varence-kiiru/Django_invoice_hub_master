"""
Management command to backfill RevenueCollection and TaxLiability records
for existing payments in the system.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from invoicing_app.payments.models import Payment
from invoicing_app.financials.models import (
    RevenueCollection,
    TaxLiability,
    FinancialPeriod,
)


class Command(BaseCommand):
    """
    Backfill financial records for existing payments.

    This command processes all confirmed payments and creates corresponding
    RevenueCollection and TaxLiability records. Safe to run multiple times
    as it skips payments that already have revenue collections.
    """

    help = "Backfill RevenueCollection and TaxLiability for existing payments"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--organization",
            type=int,
            help="Backfill only for specific organization ID",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be processed without making changes",
        )
        parser.add_argument(
            "--from-date",
            type=str,
            help="Only process payments from this date (YYYY-MM-DD format)",
        )

    def handle(self, *args, **options):
        """Execute the backfill command."""
        dry_run = options.get("dry_run", False)
        organization_id = options.get("organization")
        from_date = options.get("from_date")

        # Get confirmed payments that don't have revenue collections
        payments = Payment.objects.filter(
            status="confirmed",
            invoice__isnull=False,
        ).select_related("invoice", "invoice__organization")

        if organization_id:
            payments = payments.filter(invoice__organization_id=organization_id)

        if from_date:
            try:
                from datetime import datetime

                from_datetime = datetime.strptime(from_date, "%Y-%m-%d")
                payments = payments.filter(payment_date__gte=from_datetime)
            except ValueError:
                raise CommandError(f"Invalid date format: {from_date}. Use YYYY-MM-DD")

        # Filter out payments that already have revenue collections
        payment_ids_with_collections = RevenueCollection.objects.filter(
            payment__isnull=False
        ).values_list("payment_id", flat=True)
        payments = payments.exclude(id__in=payment_ids_with_collections)

        total_payments = payments.count()
        self.stdout.write(f"\nFound {total_payments} payments to process")

        if total_payments == 0:
            self.stdout.write(self.style.WARNING("No payments to backfill"))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING("\n=== DRY RUN MODE ===\n"))
            for payment in payments[:5]:
                self._print_payment_info(payment)
            if total_payments > 5:
                self.stdout.write(f"... and {total_payments - 5} more payments")
            return

        # Process payments in transaction
        with transaction.atomic():
            created_collections = 0
            updated_liabilities = 0
            errors = []

            for i, payment in enumerate(payments, 1):
                try:
                    created_collections += self._process_payment(payment)
                    updated_liabilities += 1

                    if i % 50 == 0:
                        self.stdout.write(f"Processed {i}/{total_payments} payments...")

                except Exception as e:
                    errors.append((payment.id, str(e)))
                    self.stdout.write(
                        self.style.ERROR(f"Error processing payment {payment.id}: {e}")
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Backfill complete!\n"
                f"  Created {created_collections} RevenueCollection records\n"
                f"  Updated {updated_liabilities} TaxLiability records"
            )
        )

        if errors:
            self.stdout.write(
                self.style.WARNING(f"\n⚠ {len(errors)} errors encountered:")
            )
            for payment_id, error in errors[:10]:
                self.stdout.write(f"  Payment {payment_id}: {error}")

    def _process_payment(self, payment):
        """
        Process a single payment and create financial records.

        Returns number of RevenueCollection records created.
        """
        invoice = payment.invoice
        organization = invoice.organization

        # Calculate revenue and tax breakdown
        total_amount = payment.amount_paid
        invoice_total = invoice.total_amount

        if invoice_total == 0:
            return 0

        revenue_pct = Decimal("1.0")
        tax_pct = Decimal("0.0")

        # Find or create financial period
        period_start = payment.payment_date.date().replace(day=1)
        if payment.payment_date.month == 12:
            period_end = period_start.replace(year=period_start.year + 1, month=1)
            period_end = period_end - timedelta(days=1)
        else:
            period_end = period_start.replace(month=period_start.month + 1)
            period_end = period_end - timedelta(days=1)

        financial_period, _ = FinancialPeriod.objects.get_or_create(
            organization=organization,
            period_type="monthly",
            start_date=period_start,
            defaults={"end_date": period_end},
        )

        # Create RevenueCollection
        revenue_collection, created = RevenueCollection.objects.get_or_create(
            payment=payment,
            defaults={
                "organization": organization,
                "invoice": invoice,
                "collected_date": payment.payment_date.date(),
                "revenue_amount": Decimal(str(total_amount * revenue_pct)),
                "tax_amount": Decimal(str(total_amount * tax_pct)),
                "tax_type": "VAT",
                "tax_rate": tax_pct * 100,
                "financial_period": financial_period,
                "status": "collected",
            },
        )

        # Update TaxLiability
        tax_liability, _ = TaxLiability.objects.get_or_create(
            organization=organization,
            financial_period=financial_period,
            tax_type="VAT",
            defaults={
                "due_date": financial_period.end_date + timedelta(days=14),
            },
        )

        # Update aggregates
        tax_liability.total_tax_collected += Decimal(str(total_amount * tax_pct))
        tax_liability.total_revenue += Decimal(str(total_amount * revenue_pct))

        # Update status based on due date
        today = timezone.now().date()
        if tax_liability.due_date < today:
            tax_liability.status = "overdue"
        elif (tax_liability.due_date - today).days <= 7:
            tax_liability.status = "due_soon"
        else:
            tax_liability.status = "pending"

        tax_liability.save()

        return 1 if created else 0

    def _print_payment_info(self, payment):
        """Print information about a payment for dry-run."""
        invoice = payment.invoice
        self.stdout.write(
            f"Payment {payment.receipt_number}: "
            f"{payment.amount_paid} ({payment.payment_date.date()}) -> "
            f"Invoice {invoice.invoice_number}"
        )
