"""
Unit tests for TaxCalculationService.
Tests VAT calculations, tax breakdown, and decimal precision.
"""
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from invoicing_app.taxes.models import TaxRate
from invoicing_app.taxes.services import TaxCalculationService


class TaxCalculationServiceTestCase(TestCase):
    """Test cases for tax and VAT calculation service."""

    def setUp(self):
        """Set up test fixtures for tax rates."""
        # Create standard VAT rate (16%)
        self.vat_16 = TaxRate.objects.create(
            code='VATX16',
            name='Standard VAT',
            rate_percentage=16,
            is_vat_applicable=True,
            effective_from=timezone.now().date(),
        )

        # Create zero-rated tax
        self.vat_zero = TaxRate.objects.create(
            code='VATZ00',
            name='Zero-Rated',
            rate_percentage=0,
            is_vat_applicable=True,
            effective_from=timezone.now().date(),
        )

        # Create exempt tax
        self.exempt = TaxRate.objects.create(
            code='VATEX',
            name='Exempt',
            rate_percentage=0,
            is_vat_applicable=False,
            effective_from=timezone.now().date(),
        )

    def test_calculate_line_vat_standard_rate(self):
        """Test VAT calculation with standard 16% rate."""
        line_amount = Decimal('100.00')
        vat = TaxCalculationService.calculate_line_vat(line_amount, self.vat_16)

        # 100 * 16% = 16.00
        self.assertEqual(vat, Decimal('16.00'))

    def test_calculate_line_vat_precision(self):
        """Test VAT calculation maintains decimal precision."""
        line_amount = Decimal('123.45')
        vat = TaxCalculationService.calculate_line_vat(line_amount, self.vat_16)

        # 123.45 * 16% = 19.752 → 19.75 (rounded)
        self.assertEqual(vat, Decimal('19.75'))

    def test_calculate_line_vat_zero_rated(self):
        """Test VAT calculation with zero-rated items."""
        line_amount = Decimal('100.00')
        vat = TaxCalculationService.calculate_line_vat(line_amount, self.vat_zero)

        self.assertEqual(vat, Decimal('0.00'))

    def test_calculate_line_vat_exempt(self):
        """Test VAT calculation with exempt items."""
        line_amount = Decimal('100.00')
        vat = TaxCalculationService.calculate_line_vat(line_amount, self.exempt)

        self.assertEqual(vat, Decimal('0.00'))

    def test_calculate_line_vat_null_rate(self):
        """Test VAT calculation with None tax rate."""
        line_amount = Decimal('100.00')
        vat = TaxCalculationService.calculate_line_vat(line_amount, None)

        self.assertEqual(vat, Decimal('0.00'))

    def test_calculate_line_vat_small_amounts(self):
        """Test VAT calculation with small amounts."""
        line_amount = Decimal('1.00')
        vat = TaxCalculationService.calculate_line_vat(line_amount, self.vat_16)

        # 1.00 * 16% = 0.16
        self.assertEqual(vat, Decimal('0.16'))

    def test_calculate_line_vat_large_amounts(self):
        """Test VAT calculation with large amounts."""
        line_amount = Decimal('10000.00')
        vat = TaxCalculationService.calculate_line_vat(line_amount, self.vat_16)

        # 10000 * 16% = 1600.00
        self.assertEqual(vat, Decimal('1600.00'))

    def test_calculate_line_total_standard_rate(self):
        """Test line total calculation (amount + VAT)."""
        line_amount = Decimal('100.00')
        total = TaxCalculationService.calculate_line_total(line_amount, self.vat_16)

        # 100 + 16 = 116.00
        self.assertEqual(total, Decimal('116.00'))

    def test_calculate_line_total_zero_rated(self):
        """Test line total with zero-rated items."""
        line_amount = Decimal('100.00')
        total = TaxCalculationService.calculate_line_total(line_amount, self.vat_zero)

        # 100 + 0 = 100.00
        self.assertEqual(total, Decimal('100.00'))

    def test_calculate_line_total_precision(self):
        """Test line total maintains precision."""
        line_amount = Decimal('123.45')
        total = TaxCalculationService.calculate_line_total(line_amount, self.vat_16)

        # 123.45 + 19.75 = 143.20
        self.assertEqual(total, Decimal('143.20'))

    def test_calculate_invoice_totals_single_item(self):
        """Test invoice totals with single line item."""
        from invoicing_app.invoices.models import Invoice, InvoiceLineItem
        from invoicing_app.clients.models import Client

        # Create test invoice with line item
        client = Client.objects.create(
            name='Test Client',
            email='test@example.com',
            phone='1234567890',
            tax_id='P123456789A'
        )

        invoice = Invoice.objects.create(
            invoice_number='TEST-001',
            client=client,
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date(),
            currency='KES'
        )

        line_item = InvoiceLineItem.objects.create(
            invoice=invoice,
            description='Test Item',
            quantity=Decimal('1'),
            unit_price=Decimal('100.00'),
            line_amount=Decimal('100.00'),
            tax_rate=self.vat_16,
            tax_amount=Decimal('16.00'),
            line_total=Decimal('116.00'),
        )

        totals = TaxCalculationService.calculate_invoice_totals([line_item])

        self.assertEqual(totals['subtotal'], Decimal('100.00'))
        self.assertEqual(totals['vat_amount'], Decimal('16.00'))
        self.assertEqual(totals['total'], Decimal('116.00'))

    def test_calculate_invoice_totals_multiple_items(self):
        """Test invoice totals with multiple line items."""
        from invoicing_app.invoices.models import Invoice, InvoiceLineItem
        from invoicing_app.clients.models import Client

        client = Client.objects.create(
            name='Test Client',
            email='test@example.com',
            phone='1234567890',
            tax_id='P123456789A'
        )

        invoice = Invoice.objects.create(
            invoice_number='TEST-002',
            client=client,
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date(),
            currency='KES'
        )

        # Item 1: 100 @ 16%
        line_item1 = InvoiceLineItem.objects.create(
            invoice=invoice,
            description='Item 1',
            quantity=Decimal('1'),
            unit_price=Decimal('100.00'),
            line_amount=Decimal('100.00'),
            tax_rate=self.vat_16,
            tax_amount=Decimal('16.00'),
            line_total=Decimal('116.00'),
        )

        # Item 2: 50 @ 0% (zero-rated)
        line_item2 = InvoiceLineItem.objects.create(
            invoice=invoice,
            description='Item 2 (Zero-rated)',
            quantity=Decimal('1'),
            unit_price=Decimal('50.00'),
            line_amount=Decimal('50.00'),
            tax_rate=self.vat_zero,
            tax_amount=Decimal('0.00'),
            line_total=Decimal('50.00'),
        )

        totals = TaxCalculationService.calculate_invoice_totals([line_item1, line_item2])

        # 100 + 50 = 150 subtotal
        # 16 + 0 = 16 VAT
        # 150 + 16 = 166 total
        self.assertEqual(totals['subtotal'], Decimal('150.00'))
        self.assertEqual(totals['vat_amount'], Decimal('16.00'))
        self.assertEqual(totals['total'], Decimal('166.00'))

    def test_calculate_invoice_totals_vat_breakdown(self):
        """Test VAT breakdown in invoice totals."""
        from invoicing_app.invoices.models import Invoice, InvoiceLineItem
        from invoicing_app.clients.models import Client

        client = Client.objects.create(
            name='Test Client',
            email='test@example.com',
            phone='1234567890',
            tax_id='P123456789A'
        )

        invoice = Invoice.objects.create(
            invoice_number='TEST-003',
            client=client,
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date(),
            currency='KES'
        )

        # Item with standard VAT
        line_item = InvoiceLineItem.objects.create(
            invoice=invoice,
            description='Standard Item',
            quantity=Decimal('1'),
            unit_price=Decimal('100.00'),
            line_amount=Decimal('100.00'),
            tax_rate=self.vat_16,
            tax_amount=Decimal('16.00'),
            line_total=Decimal('116.00'),
        )

        totals = TaxCalculationService.calculate_invoice_totals([line_item])

        # Check VAT breakdown
        self.assertIn('vat_breakdown', totals)
        self.assertEqual(totals['vat_breakdown']['standard_vat'], Decimal('16.00'))

    def test_calculate_invoice_totals_empty_items(self):
        """Test invoice totals with empty items list."""
        totals = TaxCalculationService.calculate_invoice_totals([])

        self.assertEqual(totals['subtotal'], Decimal('0.00'))
        self.assertEqual(totals['vat_amount'], Decimal('0.00'))
        self.assertEqual(totals['total'], Decimal('0.00'))


class TaxRateEdgeCasesTestCase(TestCase):
    """Test edge cases in tax calculations."""

    def setUp(self):
        """Set up test fixtures."""
        self.vat_3 = TaxRate.objects.create(
            code='VATX03',
            name='3% Tax',
            rate_percentage=3,
            is_vat_applicable=True,
            effective_from=timezone.now().date(),
        )

    def test_calculate_vat_with_odd_percentages(self):
        """Test VAT calculation with non-standard rates."""
        line_amount = Decimal('333.33')
        vat = TaxCalculationService.calculate_line_vat(line_amount, self.vat_3)

        # 333.33 * 3% = 9.9999 → 10.00
        self.assertEqual(vat, Decimal('10.00'))

    def test_calculate_vat_rounding_down(self):
        """Test that VAT rounds correctly (banker's rounding)."""
        self.vat_15 = TaxRate.objects.create(
            code='VATX15',
            name='15% Tax',
            rate_percentage=15,
            is_vat_applicable=True,
            effective_from=timezone.now().date(),
        )

        # 100.01 * 15% = 15.0015 → 15.00
        vat = TaxCalculationService.calculate_line_vat(Decimal('100.01'), self.vat_15)
        self.assertEqual(vat, Decimal('15.00'))
