"""
Tax calculation service.
Handles VAT and tax calculations for invoices and line items.
"""
from decimal import Decimal
from invoicing_app.taxes.models import TaxRate


class TaxCalculationService:
    """
    Service for calculating VAT and taxes on invoices and line items.
    """

    @staticmethod
    def calculate_line_vat(line_amount, tax_rate):
        """
        Calculate VAT for a single line item.

        Args:
            line_amount (Decimal): Line amount before VAT
            tax_rate (TaxRate): The tax rate to apply

        Returns:
            Decimal: Calculated VAT amount
        """
        if not tax_rate or tax_rate.rate_percentage is None:
            return Decimal('0.00')

        rate_decimal = Decimal(str(tax_rate.rate_percentage))
        line_decimal = Decimal(str(line_amount))
        vat = (line_decimal * rate_decimal / 100).quantize(Decimal('0.01'))
        return vat

    @staticmethod
    def calculate_line_total(line_amount, tax_rate):
        """
        Calculate total for a line item (amount + VAT).

        Args:
            line_amount (Decimal): Line amount before VAT
            tax_rate (TaxRate): The tax rate to apply

        Returns:
            Decimal: Line total (amount + VAT)
        """
        line_decimal = Decimal(str(line_amount))
        vat = TaxCalculationService.calculate_line_vat(line_amount, tax_rate)
        return (line_decimal + vat).quantize(Decimal('0.01'))

    @staticmethod
    def calculate_invoice_totals(line_items):
        """
        Calculate invoice totals from line items.

        Args:
            line_items (QuerySet or list): Invoice line items

        Returns:
            dict: {
                'subtotal': Decimal,
                'vat_amount': Decimal,
                'total': Decimal,
                'vat_breakdown': {
                    'standard_vat': Decimal,
                    'zero_rated': Decimal,
                    'exempt': Decimal,
                }
            }
        """
        subtotal = Decimal('0.00')
        vat_total = Decimal('0.00')
        standard_vat = Decimal('0.00')
        zero_rated = Decimal('0.00')
        exempt = Decimal('0.00')

        for line in line_items:
            line_amount = Decimal(str(line.line_amount))
            tax_amount = Decimal(str(line.tax_amount))

            subtotal += line_amount
            vat_total += tax_amount

            # Categorize VAT type
            if line.tax_rate.rate_percentage == 0:
                zero_rated += line_amount
            elif line.tax_rate.rate_percentage is None or line.tax_rate.rate_percentage == 0:
                if line.tax_rate.is_vat_applicable is False:
                    exempt += line_amount
                else:
                    zero_rated += line_amount
            else:
                standard_vat += tax_amount

        total = (subtotal + vat_total).quantize(Decimal('0.01'))

        return {
            'subtotal': subtotal.quantize(Decimal('0.01')),
            'vat_amount': vat_total.quantize(Decimal('0.01')),
            'total': total,
            'vat_breakdown': {
                'standard_vat': standard_vat.quantize(Decimal('0.01')),
                'zero_rated': zero_rated.quantize(Decimal('0.01')),
                'exempt': exempt.quantize(Decimal('0.01')),
            }
        }

    @staticmethod
    def get_applicable_tax_rate(product):
        """
        Get the applicable tax rate for a product.
        Respects VAT rules with priorities.

        Args:
            product: Product instance

        Returns:
            TaxRate: The applicable tax rate
        """
        # Check if there are any VAT rules for this product's tax class
        rules = product.tax_class.vat_rules.filter(is_active=True).order_by('-priority')

        if rules.exists():
            # Use highest priority rule
            return rules.first().tax_rate

        # Fall back to looking for active rate matching the tax class type
        rate_type_map = {
            'standard': 'VATX16',  # Or look up current standard rate
            'zero': 'VATZ00',
            'exempt': 'VATXEM',
        }

        code = rate_type_map.get(product.tax_class.rate_type)
        if code:
            try:
                return TaxRate.objects.get(code=code)
            except TaxRate.DoesNotExist:
                pass

        # Last resort: return first active tax rate
        return TaxRate.objects.filter(tax_type='vat').first()

    @staticmethod
    def validate_vat_amount(line_amount, tax_rate, expected_vat):
        """
        Validate that calculated VAT matches expected VAT.

        Args:
            line_amount (Decimal): Line amount
            tax_rate (TaxRate): Tax rate
            expected_vat (Decimal): Expected VAT amount

        Returns:
            bool: True if valid, False otherwise
        """
        calculated_vat = TaxCalculationService.calculate_line_vat(line_amount, tax_rate)
        # Allow small rounding differences (up to 0.01)
        return abs(calculated_vat - Decimal(str(expected_vat))) <= Decimal('0.01')
