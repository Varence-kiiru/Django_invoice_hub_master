"""
Quotation services.
Handles quote number generation, quote-to-invoice conversion, and status management.
"""
from django.db import transaction
from django.utils import timezone
from invoicing_app.invoices.services import TaxCalculationService, InvoiceNumberService
from invoicing_app.invoices.models import Invoice, InvoiceLineItem
from .models import QuoteNumberSequence, Quote, QuoteLineItem


# ━━━ Quote Number Generation ━━━
class QuoteNumberService:
    """
    Service for generating unique, non-gapped quote numbers per prefix/year.
    Uses SELECT FOR UPDATE for concurrent-safe incrementing.
    Pattern replicated from InvoiceNumberService.
    """

    @staticmethod
    def generate_next_number(prefix='QUOTE', year=None):
        """
        Generate the next quote number for the given prefix and year.

        Args:
            prefix (str): Quote prefix (default 'QUOTE')
            year (int): Calendar year (default: current year)

        Returns:
            str: Quote number (e.g., 'QUOTE-2026-0001')

        Raises:
            RuntimeError: If database lock cannot be acquired
        """
        if year is None:
            year = timezone.now().year

        with transaction.atomic():
            # Lock the row to prevent concurrent increments
            seq_qs = QuoteNumberSequence.objects.select_for_update().filter(
                prefix=prefix,
                year=year
            )

            # Get or create the sequence row
            try:
                seq = seq_qs.get()
            except QuoteNumberSequence.DoesNotExist:
                # Create new sequence row
                seq = QuoteNumberSequence.objects.create(
                    prefix=prefix,
                    year=year,
                    next_sequence=1
                )

            # Get current sequence value
            current_seq = seq.next_sequence

            # Increment for next call
            seq.next_sequence += 1
            seq.save(update_fields=['next_sequence'])

            # Generate and return quote number
            quote_number = f"{prefix}-{year}-{current_seq:04d}"
            return quote_number

    @staticmethod
    def get_preview_number(prefix='QUOTE', year=None):
        """
        Get preview of next quote number WITHOUT making any changes.

        Args:
            prefix (str): Quote prefix
            year (int): Calendar year (default: current year)

        Returns:
            str: Preview of quote number
        """
        if year is None:
            year = timezone.now().year

        next_seq = QuoteNumberService.get_next_sequence(prefix, year)
        return f"{prefix}-{year}-{next_seq:04d}"

    @staticmethod
    def get_next_sequence(prefix='QUOTE', year=None):
        """
        Get the next sequence number WITHOUT incrementing it.
        Useful for previewing the next quote number.

        Args:
            prefix (str): Quote prefix
            year (int): Calendar year (default: current year)

        Returns:
            int: The next sequence number
        """
        if year is None:
            year = timezone.now().year

        try:
            seq = QuoteNumberSequence.objects.get(prefix=prefix, year=year)
            return seq.next_sequence
        except QuoteNumberSequence.DoesNotExist:
            return 1


# ━━━ Quote to Invoice Conversion ━━━
class QuoteConversionService:
    """
    The KEY SERVICE for quotations.
    Handles: Quote → Invoice transformation.
    """

    @staticmethod
    def convert_quote_to_invoice(quote, invoice_date=None, due_date=None):
        """
        Convert accepted quote to invoice.

        Args:
            quote: Quote object (must be in 'accepted' status)
            invoice_date: Date for the invoice (default: today)
            due_date: Due date (required - typically invoice_date + term)

        Returns:
            Invoice: Newly created invoice

        Raises:
            ValueError: If quote status is not 'accepted'
        """
        if quote.status != 'accepted':
            raise ValueError(
                f"Cannot convert {quote.status} quote to invoice. "
                f"Only 'accepted' quotes can be converted."
            )

        # Already converted?
        if quote.converted_invoice:
            return quote.converted_invoice

        # Defaults
        if invoice_date is None:
            invoice_date = timezone.now().date()
        if due_date is None:
            due_date = invoice_date

        with transaction.atomic():
            # 1. Generate invoice number
            from invoicing_app.core.models import CompanySettings
            try:
                settings = CompanySettings.objects.get()
                prefix = settings.invoice_prefix
            except CompanySettings.DoesNotExist:
                prefix = 'INV'
            invoice_number = InvoiceNumberService.generate_next_number(prefix=prefix)

            # 2. Create invoice with quote's data
            invoice = Invoice.objects.create(
                invoice_number=invoice_number,
                client=quote.client,
                invoice_date=invoice_date,
                due_date=due_date,
                status='draft',
                description=quote.description,
                currency=quote.currency,

                # Copy totals (already calculated)
                subtotal_amount=quote.subtotal_amount,
                vat_amount=quote.vat_amount,
                total_amount=quote.total_amount,
                amount_due=quote.total_amount,  # No payments yet
                amount_paid=0,

                # Audit trail
                created_by=quote.created_by,
            )

            # 3. Copy each line item
            for quote_line in quote.line_items.all():
                InvoiceLineItem.objects.create(
                    invoice=invoice,
                    product=quote_line.product,
                    description=quote_line.description,
                    quantity=quote_line.quantity,
                    unit_price=quote_line.unit_price,
                    line_amount=quote_line.line_amount,
                    tax_rate=quote_line.tax_rate,
                    tax_amount=quote_line.tax_amount,
                    line_total=quote_line.line_total,
                    notes=quote_line.notes,
                    sort_order=quote_line.sort_order,
                )

            # 4. Update quote to mark as converted
            quote.converted_invoice = invoice
            quote.status = 'converted'
            quote.converted_at = timezone.now()
            quote.updated_by = quote.created_by
            quote.save(update_fields=[
                'converted_invoice', 'status', 'converted_at', 'updated_by'
            ])

            return invoice


# ━━━ Quote Status Transitions ━━━
class QuoteStatusService:
    """
    Manages valid quote status transitions.
    Similar pattern to InvoiceStatusService but with quote-specific states.
    """

    VALID_TRANSITIONS = {
        'draft': ['sent', 'archived'],
        'sent': ['viewed', 'rejected', 'archived'],
        'viewed': ['accepted', 'rejected', 'archived'],
        'accepted': ['converted', 'archived'],
        'rejected': ['archived'],
        'expired': ['archived'],
        'converted': [],
        'archived': [],
    }

    @staticmethod
    def can_transition(current_status, new_status):
        """Check if status transition is valid."""
        return new_status in QuoteStatusService.VALID_TRANSITIONS.get(
            current_status, []
        )

    @staticmethod
    def transition_quote(quote, new_status, actor=None, reason=None):
        """
        Safely move quote to new status.

        Args:
            quote: Quote object
            new_status: Target status
            actor: User making the change
            reason: Reason (e.g., rejection reason)

        Returns:
            bool: True if successful, False if invalid transition
        """
        if not QuoteStatusService.can_transition(quote.status, new_status):
            return False

        quote.status = new_status

        # Update metadata based on status
        if new_status == 'sent':
            quote.sent_at = timezone.now()
        elif new_status == 'viewed':
            quote.viewed_at = timezone.now()
        elif new_status == 'accepted':
            quote.accepted_at = timezone.now()
        elif new_status == 'rejected':
            quote.rejected_at = timezone.now()
            if reason:
                quote.rejection_reason = reason
        elif new_status == 'expired':
            quote.expired_at = timezone.now()

        if actor:
            quote.updated_by = actor

        quote.save()
        return True
