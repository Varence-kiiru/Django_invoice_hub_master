"""
Invoice number generation service.
Handles concurrent-safe invoice number generation using database-level locking.
"""
from django.db import transaction, connection
from django.utils import timezone
from invoicing_app.invoices.models import InvoiceNumberSequence


class InvoiceNumberService:
    """
    Service for generating unique, non-gapped invoice numbers per prefix/year.
    Uses SELECT FOR UPDATE for concurrent-safe incrementing.
    """

    @staticmethod
    def generate_next_number(prefix='OG-INV', year=None):
        """
        Generate the next invoice number for the given prefix and year.

        Args:
            prefix (str): Invoice prefix (default 'OG-INV')
            year (int): Calendar year (default: current year)

        Returns:
            str: Invoice number (e.g., 'OG-INV-2026-0001')

        Raises:
            RuntimeError: If database lock cannot be acquired
        """
        if year is None:
            year = timezone.now().year

        with transaction.atomic():
            # Lock the row to prevent concurrent increments
            seq_qs = InvoiceNumberSequence.objects.select_for_update().filter(
                prefix=prefix,
                year=year
            )

            # Get or create the sequence row
            try:
                seq = seq_qs.get()
            except InvoiceNumberSequence.DoesNotExist:
                # Create new sequence row
                seq = InvoiceNumberSequence.objects.create(
                    prefix=prefix,
                    year=year,
                    next_sequence=1
                )

            # Get current sequence value
            current_seq = seq.next_sequence

            # Increment for next call
            seq.next_sequence += 1
            seq.save(update_fields=['next_sequence'])

            # Generate and return invoice number
            invoice_number = f"{prefix}-{year}-{current_seq:04d}"
            return invoice_number

    @staticmethod
    def reserve_number(prefix='INV', year=None):
        """
        Pre-reserve an invoice number (useful for drafts).
        Increments sequence without returning the number.

        Args:
            prefix (str): Invoice prefix
            year (int): Calendar year (default: current year)

        Returns:
            int: The next available sequence number
        """
        return InvoiceNumberService.generate_next_number(prefix, year)

    @staticmethod
    def get_next_sequence(prefix='INV', year=None):
        """
        Get the next sequence number WITHOUT incrementing it.
        Useful for previewing the next invoice number.

        Args:
            prefix (str): Invoice prefix
            year (int): Calendar year (default: current year)

        Returns:
            int: The next sequence number
        """
        if year is None:
            year = timezone.now().year

        try:
            seq = InvoiceNumberSequence.objects.get(prefix=prefix, year=year)
            return seq.next_sequence
        except InvoiceNumberSequence.DoesNotExist:
            return 1

    @staticmethod
    def get_preview_number(prefix='INV', year=None):
        """
        Get preview of next invoice number WITHOUT making any changes.

        Args:
            prefix (str): Invoice prefix
            year (int): Calendar year (default: current year)

        Returns:
            str: Preview of invoice number
        """
        if year is None:
            year = timezone.now().year

        next_seq = InvoiceNumberService.get_next_sequence(prefix, year)
        return f"{prefix}-{year}-{next_seq:04d}"


class TaxCalculationService:
    """Service for calculating taxes on invoices and line items."""
    
    @staticmethod
    def calculate_tax_amount(base_amount, tax_rate):
        """
        Calculate tax amount for a given base amount and tax rate.
        
        Args:
            base_amount: Decimal - amount to calculate tax on
            tax_rate: TaxRate object or rate percentage
        
        Returns: Decimal - calculated tax amount
        """
        from decimal import Decimal
        from invoicing_app.taxes.models import TaxRate
        
        if isinstance(tax_rate, TaxRate):
            rate = tax_rate.rate_percentage
        else:
            rate = Decimal(str(tax_rate))
        
        return (Decimal(str(base_amount)) * rate) / 100
    
    @staticmethod
    def calculate_line_item_totals(product_amount, tax_rate_obj):
        """
        Calculate line item totals including tax.
        
        Returns: dict with line_subtotal, tax_amount, line_total
        """
        from decimal import Decimal
        
        product_amount = Decimal(str(product_amount))
        tax_amount = TaxCalculationService.calculate_tax_amount(
            product_amount, tax_rate_obj
        )
        line_total = product_amount + tax_amount
        
        return {
            'line_subtotal': product_amount,
            'tax_amount': tax_amount,
            'line_total': line_total,
        }
    
    @staticmethod
    def calculate_invoice_totals(line_items):
        """
        Calculate invoice totals from line items.
        
        Args:
            line_items: QuerySet of InvoiceLineItem objects
        
        Returns: dict with subtotal, vat_amount, total_amount
        """
        from decimal import Decimal
        from django.db.models import Sum
        
        if isinstance(line_items, list):
            subtotal = Decimal(str(sum(
                item['line_subtotal'] if isinstance(item, dict) else item.line_subtotal 
                for item in line_items
            )))
            vat_total = Decimal(str(sum(
                item['tax_amount'] if isinstance(item, dict) else item.tax_amount 
                for item in line_items
            )))
        else:
            subtotal = line_items.aggregate(
                total=Sum('line_subtotal')
            )['total'] or Decimal('0.00')
            vat_total = line_items.aggregate(
                total=Sum('tax_amount')
            )['total'] or Decimal('0.00')
        
        total_amount = subtotal + vat_total
        
        return {
            'subtotal_amount': subtotal,
            'vat_amount': vat_total,
            'total_amount': total_amount,
        }


class PaymentReconciliationService:
    """Service for payment reconciliation and matching."""
    
    @staticmethod
    def match_payment_to_invoice(invoice, amount):
        """
        Determine if payment fully or partially satisfies invoice.
        
        Returns: dict with is_fully_paid, amount_remaining
        """
        from decimal import Decimal
        
        amount = Decimal(str(amount))
        if amount >= invoice.amount_due:
            return {
                'is_fully_paid': True,
                'amount_remaining': Decimal('0.00'),
                'amount_overpaid': amount - invoice.amount_due,
            }
        else:
            return {
                'is_fully_paid': False,
                'amount_remaining': invoice.amount_due - amount,
                'amount_overpaid': Decimal('0.00'),
            }
    
    @staticmethod
    def reconcile_outstanding_invoices(client=None):
        """
        Get outstanding invoices for reconciliation.
        
        Args:
            client: Client object (optional) to filter by single client
        
        Returns: QuerySet of outstanding invoices
        """
        from invoicing_app.invoices.models import Invoice
        
        outstanding = Invoice.objects.filter(
            is_active=True,
            status__in=['issued', 'sent', 'viewed', 'overdue'],
            amount_due__gt=0
        )
        
        if client:
            outstanding = outstanding.filter(client=client)
        
        return outstanding.select_related('client').order_by('due_date')
    
    @staticmethod
    def get_aging_buckets(days_list=None):
        """
        Get outstanding invoices grouped by age buckets.
        
        Args:
            days_list: List of day boundaries (default: [30, 60, 90])
        
        Returns: dict with aged invoice counts and amounts
        """
        from django.utils import timezone
        from datetime import timedelta
        
        if days_list is None:
            days_list = [30, 60, 90]
        
        today = timezone.now().date()
        outstanding = PaymentReconciliationService.reconcile_outstanding_invoices()
        
        buckets = {}
        prev_days = 0
        
        for max_days in days_list:
            cutoff_date = today - timedelta(days=max_days)
            prev_cutoff = today - timedelta(days=prev_days) if prev_days > 0 else today
            
            count = outstanding.filter(
                due_date__gte=cutoff_date,
                due_date__lt=prev_cutoff
            ).count()
            
            buckets[f'{prev_days}-{max_days} days'] = count
            prev_days = max_days
        
        # Add over 90 days
        cutoff_date = today - timedelta(days=days_list[-1])
        count = outstanding.filter(due_date__lt=cutoff_date).count()
        buckets['Over 90 days'] = count
        
        return buckets


class InvoiceStatusService:
    """Service for managing invoice status transitions."""
    
    VALID_TRANSITIONS = {
        'draft': ['issued', 'cancelled'],
        'issued': ['sent', 'cancelled'],
        'sent': ['viewed', 'cancelled'],
        'viewed': ['paid', 'overdue', 'cancelled'],
        'paid': [],
        'overdue': ['paid', 'cancelled'],
        'cancelled': [],
    }
    
    @staticmethod
    def can_transition(current_status, new_status):
        """Check if status transition is valid."""
        return new_status in InvoiceStatusService.VALID_TRANSITIONS.get(
            current_status, []
        )
    
    @staticmethod
    def transition_invoice(invoice, new_status, actor=None):
        """
        Safely transition invoice to new status.
        
        Returns: bool - success or failure
        """
        if not InvoiceStatusService.can_transition(invoice.status, new_status):
            return False
        
        invoice.status = new_status
        
        if new_status == 'issued':
            invoice.issued_at = timezone.now()
        elif new_status == 'sent':
            invoice.sent_at = timezone.now()
        elif new_status == 'viewed':
            invoice.viewed_at = timezone.now()
        elif new_status == 'cancelled':
            invoice.cancelled_at = timezone.now()
        
        if actor:
            invoice.updated_by = actor
        invoice.save()
        
        return True
