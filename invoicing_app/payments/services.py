"""
Payment services.
"""

from django.db import transaction
from django.utils import timezone
from .models import PaymentReceiptNumberSequence


class PaymentReceiptNumberService:
    """
    Service for generating unique, non-gapped payment receipt numbers per prefix/year.
    Uses SELECT FOR UPDATE for concurrent-safe incrementing.
    """

    @staticmethod
    def generate_next_number(prefix="REC", year=None):
        """
        Generate the next payment receipt number for the given prefix and year.

        Args:
            prefix (str): Payment receipt prefix (default 'REC')
            year (int): Calendar year (default: current year)

        Returns:
            str: Payment receipt number (e.g., 'REC-2026-0001')

        Raises:
            RuntimeError: If database lock cannot be acquired
        """
        if year is None:
            year = timezone.now().year

        with transaction.atomic():
            # Lock the row to prevent concurrent increments
            seq_qs = PaymentReceiptNumberSequence.objects.select_for_update().filter(
                prefix=prefix, year=year
            )

            # Get or create the sequence row
            try:
                seq = seq_qs.get()
            except PaymentReceiptNumberSequence.DoesNotExist:
                # Create new sequence row
                seq = PaymentReceiptNumberSequence.objects.create(
                    prefix=prefix, year=year, next_sequence=1
                )

            # Get current sequence value
            current_seq = seq.next_sequence

            # Increment for next call
            seq.next_sequence += 1
            seq.save(update_fields=["next_sequence"])

            # Generate and return receipt number
            receipt_number = f"{prefix}-{year}-{current_seq:04d}"
            return receipt_number

    @staticmethod
    def reserve_number(prefix="REC", year=None):
        """
        Pre-reserve a receipt number.
        Increments sequence without returning the number.

        Args:
            prefix (str): Payment receipt prefix
            year (int): Calendar year (default: current year)

        Returns:
            int: The next available sequence number
        """
        return PaymentReceiptNumberService.generate_next_number(prefix, year)
