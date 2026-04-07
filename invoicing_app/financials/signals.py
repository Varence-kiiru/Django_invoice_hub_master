"""
Signals for financial tracking.
Auto-creates revenue collection and tax liability records when payments are confirmed.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import logging

from invoicing_app.payments.models import Payment
from invoicing_app.organizations.models import Organization
from .models import RevenueCollection, TaxLiability, FinancialPeriod

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Payment)
def create_revenue_collection_on_payment(
    sender, instance, created, update_fields, **kwargs
):
    """
    Auto-create RevenueCollection record when payment is confirmed.
    Also updates/creates TaxLiability for the period.
    Handles both newly created payments AND status updates to confirmed.
    """
    # Only process confirmed payments
    if instance.status != "confirmed":
        return

    # Check if revenue collection already exists (prevent duplicates)
    if hasattr(instance, "revenue_collection"):
        # Already has a revenue collection, skip
        return

    try:
        # Check if RevenueCollection already exists for this payment
        from .models import RevenueCollection as RC

        if RC.objects.filter(payment=instance).exists():
            return  # Already created
    except Exception:
        pass  # If table doesn't exist, continue

    try:
        with transaction.atomic():
            # Get invoice and organization
            invoice = instance.invoice
            organization = getattr(invoice, "organization", None)

            if organization is None and hasattr(invoice, "client"):
                organization = getattr(invoice.client, "organization", None)

            if organization is None:
                organization = Organization.objects.first()

            if organization is None:
                raise ValueError(
                    "Unable to determine organization for RevenueCollection"
                )

            # Find or create financial period
            collected_date = timezone.now().date()
            year = collected_date.year
            month = collected_date.month

            # Calculate month range for monthly period
            from datetime import date
            from calendar import monthrange

            _, last_day = monthrange(year, month)
            start_date = date(year, month, 1)
            end_date = date(year, month, last_day)

            financial_period, _ = FinancialPeriod.objects.get_or_create(
                organization=organization,
                period_type="monthly",
                start_date=start_date,
                end_date=end_date,
            )

            # Check if revenue collection already exists
            if hasattr(instance, "revenue_collection"):
                return  # Already created

            # Calculate revenue and tax
            payment_amount = Decimal(str(instance.amount))  # Ensure Decimal type

            # Get tax info from invoice - ensure all values are Decimal
            total_amount = (
                Decimal(str(invoice.total_amount))
                if invoice.total_amount
                else Decimal("0")
            )
            subtotal_amount = (
                Decimal(str(invoice.subtotal_amount))
                if invoice.subtotal_amount
                else Decimal("0")
            )
            vat_amount = (
                Decimal(str(invoice.vat_amount)) if invoice.vat_amount else Decimal("0")
            )

            # Get actual tax rates applied to this invoice's line items
            line_items = invoice.line_items.all()
            tax_type = "VAT"  # Default

            if line_items.exists():
                # Calculate weighted average tax rate based on line amounts
                total_line_amount = Decimal("0")
                weighted_tax = Decimal("0")
                unique_rates = set()  # Track unique tax rates

                for line_item in line_items:
                    if line_item.tax_rate:
                        line_amt = (
                            Decimal(str(line_item.line_amount))
                            if line_item.line_amount
                            else Decimal("0")
                        )
                        tax_rate_pct = (
                            Decimal(str(line_item.tax_rate.rate_percentage))
                            if line_item.tax_rate.rate_percentage
                            else Decimal("0")
                        )

                        total_line_amount += line_amt
                        weighted_tax += line_amt * tax_rate_pct
                        unique_rates.add(float(tax_rate_pct))  # Track unique rates

                        if line_item.tax_rate.tax_type:
                            tax_type = line_item.tax_rate.get_tax_type_display()

                # Calculate weighted average: (sum of line_amount * rate%) / total_line_amount
                if total_line_amount > 0:
                    calculated_tax_rate = (weighted_tax / total_line_amount).quantize(
                        Decimal("0.01")
                    )
                else:
                    calculated_tax_rate = Decimal("0")

                # Update tax_type to reflect if rates are mixed
                if len(unique_rates) > 1:
                    tax_type = "Mixed Rates"
            else:
                # Fallback to ratio calculation if no line items
                if total_amount > 0:
                    calculated_tax_rate = (vat_amount / total_amount) * Decimal("100")
                else:
                    calculated_tax_rate = Decimal("0")

            # Calculate ratios safely with Decimal arithmetic
            if total_amount > 0:
                subtotal_ratio = subtotal_amount / total_amount
                vat_ratio = vat_amount / total_amount
            else:
                subtotal_ratio = Decimal("0")
                vat_ratio = Decimal("0")

            # Allocate payment proportionally to revenue and tax
            # All values are now Decimal type - safe to multiply
            revenue_amount = payment_amount * subtotal_ratio
            tax_amount = payment_amount * vat_ratio

            # Create revenue collection
            revenue_collection = RevenueCollection.objects.create(
                organization=organization,
                payment=instance,
                invoice=invoice,
                financial_period=financial_period,
                collected_date=collected_date,
                revenue_amount=revenue_amount.quantize(Decimal("0.01")),
                tax_amount=tax_amount.quantize(Decimal("0.01")),
                total_amount=payment_amount,
                tax_type=tax_type,
                tax_rate=(
                    calculated_tax_rate.quantize(Decimal("0.01"))
                    if calculated_tax_rate
                    else Decimal("0")
                ),
                status="collected",
            )

            logger.info(
                f"Created revenue collection {revenue_collection.id} for payment {instance.receipt_number}"
            )

            # Update or create tax liability
            update_tax_liability_for_period(organization, financial_period)

    except Exception as e:
        logger.error(
            f"Error creating revenue collection for payment {instance.receipt_number}: {str(e)}"
        )


def update_tax_liability_for_period(organization, financial_period):
    """
    Recalculate tax liability for a given organization and period.
    Aggregates all revenue collections in the period.
    """
    try:
        # Aggregate revenue collections
        from django.db.models import Sum

        collections = RevenueCollection.objects.filter(
            organization=organization,
            financial_period=financial_period,
            status__in=["collected", "pending_remittance"],
        )

        aggregates = collections.aggregate(
            total_revenue=Sum("revenue_amount"),
            total_tax=Sum("tax_amount"),
        )

        total_revenue = aggregates["total_revenue"] or Decimal("0.00")
        total_tax = aggregates["total_tax"] or Decimal("0.00")

        # Determine status
        today = timezone.now().date()
        due_date = financial_period.end_date
        from datetime import timedelta

        if due_date:
            due_date = due_date + timedelta(days=30)  # Due 30 days after period end

        if total_tax == 0:
            status = "pending"
        elif due_date and today > due_date:
            status = "overdue"
        elif due_date and (due_date - today).days <= 7:
            status = "due_soon"
        else:
            status = "pending"

        # Update or create tax liability
        tax_liability, created = TaxLiability.objects.update_or_create(
            organization=organization,
            financial_period=financial_period,
            tax_type="VAT",
            defaults={
                "total_revenue": total_revenue,
                "total_tax_collected": total_tax,
                "final_liability": total_tax,  # Before penalties/discounts
                "status": status,
                "due_date": due_date,
            },
        )

        action = "Created" if created else "Updated"
        logger.info(
            f"{action} tax liability {tax_liability.id}: {total_tax} for period {financial_period}"
        )

    except Exception as e:
        logger.error(f"Error updating tax liability: {str(e)}")
