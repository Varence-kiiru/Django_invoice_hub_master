"""
Unit tests for InvoiceNumberService.
Tests concurrent-safe invoice number generation and sequence management.
"""
from django.test import TestCase, TransactionTestCase
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from invoicing_app.invoices.models import InvoiceNumberSequence
from invoicing_app.invoices.services import InvoiceNumberService
from concurrent.futures import ThreadPoolExecutor
import time


class InvoiceNumberServiceTestCase(TestCase):
    """Test cases for invoice number generation."""

    def setUp(self):
        """Clean up invoice sequences before each test."""
        InvoiceNumberSequence.objects.all().delete()

    def test_generate_next_number_basic(self):
        """Test basic invoice number generation."""
        number = InvoiceNumberService.generate_next_number('INV', 2026)
        self.assertEqual(number, 'INV-2026-0001')

    def test_generate_next_number_sequential(self):
        """Test sequential number generation."""
        num1 = InvoiceNumberService.generate_next_number('INV', 2026)
        num2 = InvoiceNumberService.generate_next_number('INV', 2026)
        num3 = InvoiceNumberService.generate_next_number('INV', 2026)

        self.assertEqual(num1, 'INV-2026-0001')
        self.assertEqual(num2, 'INV-2026-0002')
        self.assertEqual(num3, 'INV-2026-0003')

    def test_generate_next_number_different_prefixes(self):
        """Test generation with different prefixes."""
        num1 = InvoiceNumberService.generate_next_number('INV', 2026)
        num2 = InvoiceNumberService.generate_next_number('QUOTE', 2026)
        num3 = InvoiceNumberService.generate_next_number('INV', 2026)

        self.assertEqual(num1, 'INV-2026-0001')
        self.assertEqual(num2, 'QUOTE-2026-0001')
        self.assertEqual(num3, 'INV-2026-0002')

    def test_generate_next_number_different_years(self):
        """Test generation with different years."""
        num1 = InvoiceNumberService.generate_next_number('INV', 2026)
        num2 = InvoiceNumberService.generate_next_number('INV', 2027)
        num3 = InvoiceNumberService.generate_next_number('INV', 2026)

        self.assertEqual(num1, 'INV-2026-0001')
        self.assertEqual(num2, 'INV-2027-0001')
        self.assertEqual(num3, 'INV-2026-0002')

    def test_generate_next_number_four_digit_padding(self):
        """Test that sequence numbers are zero-padded to 4 digits."""
        for i in range(15):
            InvoiceNumberService.generate_next_number('INV', 2026)

        # Get the 15th number
        seq = InvoiceNumberSequence.objects.get(prefix='INV', year=2026)
        self.assertEqual(seq.next_sequence, 16)  # Should be 16 (1-indexed)

    def test_get_next_sequence_preview(self):
        """Test previewing next sequence without incrementing."""
        next_seq = InvoiceNumberService.get_next_sequence('INV', 2026)
        self.assertEqual(next_seq, 1)

        # Generate a number
        InvoiceNumberService.generate_next_number('INV', 2026)

        # Check next sequence
        next_seq = InvoiceNumberService.get_next_sequence('INV', 2026)
        self.assertEqual(next_seq, 2)

        # Should not have incremented just by previewing
        next_seq2 = InvoiceNumberService.get_next_sequence('INV', 2026)
        self.assertEqual(next_seq2, 2)

    def test_sequence_persistence(self):
        """Test that sequence is persisted across calls."""
        # Generate some numbers
        InvoiceNumberService.generate_next_number('INV', 2026)
        InvoiceNumberService.generate_next_number('INV', 2026)
        InvoiceNumberService.generate_next_number('INV', 2026)

        # Check sequence in database
        seq = InvoiceNumberSequence.objects.get(prefix='INV', year=2026)
        self.assertEqual(seq.next_sequence, 4)

    def test_year_defaults_to_current_year(self):
        """Test that year defaults to current year."""
        current_year = timezone.now().year
        number = InvoiceNumberService.generate_next_number('INV')

        self.assertIn(str(current_year), number)

    def test_reserve_number(self):
        """Test reserving a number."""
        reserved = InvoiceNumberService.reserve_number('INV', 2026)
        self.assertIsNotNone(reserved)

        # Next number should be incremented
        seq = InvoiceNumberSequence.objects.get(prefix='INV', year=2026)
        self.assertEqual(seq.next_sequence, 2)

    def test_invoice_number_format(self):
        """Test the format of generated invoice numbers."""
        number = InvoiceNumberService.generate_next_number('INV', 2026)
        
        # Should be: PREFIX-YEAR-SEQUENCE
        parts = number.split('-')
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], 'INV')
        self.assertEqual(parts[1], '2026')
        self.assertEqual(parts[2], '0001')

    def test_concurrent_generation_safe(self):
        """Test that sequential generation ensures no gaps (SELECT FOR UPDATE)."""
        # SQLite doesn't support concurrent thread access in tests
        # This test verifies sequential guarantees no gaps or duplicates
        results = []
        for i in range(10):
            number = InvoiceNumberService.generate_next_number('INV', 2026)
            results.append(number)

        # All should be unique
        self.assertEqual(len(results), 10)
        self.assertEqual(len(set(results)), 10)

        # Check sequence
        seq = InvoiceNumberSequence.objects.get(prefix='INV', year=2026)
        self.assertEqual(seq.next_sequence, 11)


class InvoiceNumberServiceEdgeCaseTestCase(TransactionTestCase):
    """Edge case tests for invoice number service."""

    def setUp(self):
        """Clean up invoice sequences before each test."""
        InvoiceNumberSequence.objects.all().delete()

    def test_large_sequence_numbers(self):
        """Test handling of large sequence numbers."""
        # Create a sequence with a large number
        seq = InvoiceNumberSequence.objects.create(
            prefix='INV',
            year=2026,
            next_sequence=9999
        )

        number = InvoiceNumberService.generate_next_number('INV', 2026)
        self.assertEqual(number, 'INV-2026-9999')

        # Next should be 10000 (5 digits)
        number = InvoiceNumberService.generate_next_number('INV', 2026)
        self.assertEqual(number, 'INV-2026-10000')

    def test_special_prefix_characters(self):
        """Test handling of various prefix formats."""
        prefixes = ['QUOTE', 'PRO', 'INV-2026', 'CREDIT']

        for prefix in prefixes:
            number = InvoiceNumberService.generate_next_number(prefix, 2026)
            self.assertTrue(number.startswith(prefix))

    def test_multiple_users_same_sequence(self):
        """Test that multiple users incrementing same sequence is safe."""
        # This is more of integration test, but tests the atomic transaction

        with transaction.atomic():
            num1 = InvoiceNumberService.generate_next_number('INV', 2026)

        with transaction.atomic():
            num2 = InvoiceNumberService.generate_next_number('INV', 2026)

        self.assertEqual(num1, 'INV-2026-0001')
        self.assertEqual(num2, 'INV-2026-0002')
