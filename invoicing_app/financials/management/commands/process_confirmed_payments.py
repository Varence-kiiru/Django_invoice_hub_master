"""Management command to manually trigger financial record creation for confirmed payments."""

from django.core.management.base import BaseCommand
from invoicing_app.payments.models import Payment
from invoicing_app.financials.signals import create_revenue_collection_on_payment


class Command(BaseCommand):
    help = "Process confirmed payments and create revenue collections"

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Process all confirmed payments without existing revenue collections",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force recreate even if revenue collection exists",
        )

    def handle(self, *args, **options):
        # Get confirmed payments without revenue collections
        payments = Payment.objects.filter(status="confirmed")

        if not options.get("force"):
            payments = payments.exclude(revenue_collection__isnull=False)

        count = 0
        for payment in payments:
            try:
                # Manually trigger the signal
                create_revenue_collection_on_payment(
                    sender=Payment,
                    instance=payment,
                    created=False,
                    update_fields=None,
                )
                count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Processed payment: {payment.receipt_number}")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Error processing payment {payment.receipt_number}: {str(e)}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(f"\n✓ Successfully processed {count} payments")
        )
