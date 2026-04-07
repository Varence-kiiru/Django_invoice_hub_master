"""
Tests for financial tracking system.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date
from invoicing_app.organizations.models import Organization
from invoicing_app.clients.models import Client
from invoicing_app.invoices.models import Invoice
from invoicing_app.payments.models import Payment, PaymentMethod
from invoicing_app.financials.models import (
    FinancialPeriod,
    RevenueCollection,
    TaxLiability,
)


class FinancialPeriodModelTest(TestCase):
    """Test cases for FinancialPeriod model."""

    def setUp(self):
        """Set up test data."""
        self.organization = Organization.objects.create(
            name="Test Company",
            slug="test-company",
            admin_email="admin@test-company.com",
        )

    def test_create_monthly_period(self):
        """Test creating a monthly financial period."""
        period = FinancialPeriod.objects.create(
            organization=self.organization,
            period_type="monthly",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )
        self.assertEqual(period.period_type, "monthly")
        self.assertEqual(str(period), "January 2024")

    def test_create_quarterly_period(self):
        """Test creating a quarterly financial period."""
        period = FinancialPeriod.objects.create(
            organization=self.organization,
            period_type="quarterly",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
        )
        self.assertEqual(period.period_type, "quarterly")
        self.assertEqual(str(period), "Q1 2024")

    def test_create_annual_period(self):
        """Test creating an annual financial period."""
        period = FinancialPeriod.objects.create(
            organization=self.organization,
            period_type="annual",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
        self.assertEqual(period.period_type, "annual")
        self.assertEqual(str(period), "2024")


class RevenueCollectionModelTest(TestCase):
    """Test cases for RevenueCollection model."""

    def setUp(self):
        """Set up test data."""
        self.organization = Organization.objects.create(
            name="Test Company",
            slug="test-company",
            admin_email="admin@test-company.com",
        )
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )
        self.period = FinancialPeriod.objects.create(
            organization=self.organization,
            period_type="monthly",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        self.client = Client.objects.create(
            name="Test Client",
            client_type="business",
            email="client@test-company.com",
        )

        self.invoice = Invoice.objects.create(
            client=self.client,
            invoice_number="INV-001",
            invoice_date=date(2024, 1, 15),
            due_date=date(2024, 2, 15),
            status="issued",
            created_by=self.user,
        )

        self.payment_method = PaymentMethod.objects.create(name="Bank Transfer")

        self.payment = Payment.objects.create(
            invoice=self.invoice,
            amount=Decimal("1000.00"),
            payment_method=self.payment_method,
            status="pending",  # Create as pending first
        )

    def test_create_revenue_collection(self):
        """Test creating a revenue collection manually."""
        # Don't use payment with confirmed status to avoid auto-signal
        # Instead create a separate payment for manual test
        test_payment = Payment.objects.create(
            invoice=self.invoice,
            amount=Decimal("1000.00"),
            payment_method=self.payment_method,
            status="pending",
        )

        collection = RevenueCollection.objects.create(
            organization=self.organization,
            invoice=self.invoice,
            payment=test_payment,
            collected_date=date(2024, 1, 20),
            revenue_amount=Decimal("850.00"),
            tax_amount=Decimal("150.00"),
            total_amount=Decimal("1000.00"),
            tax_type="VAT",
            tax_rate=Decimal("15.0"),
            financial_period=self.period,
        )
        self.assertEqual(collection.revenue_amount, Decimal("850.00"))
        self.assertEqual(collection.tax_amount, Decimal("150.00"))
        self.assertEqual(collection.total_amount, Decimal("1000.00"))


class TaxLiabilityModelTest(TestCase):
    """Test cases for TaxLiability model."""

    def setUp(self):
        """Set up test data."""
        self.organization = Organization.objects.create(
            name="Test Company",
            slug="test-company",
            admin_email="admin@test-company.com",
        )
        self.period = FinancialPeriod.objects.create(
            organization=self.organization,
            period_type="monthly",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

    def test_create_tax_liability(self):
        """Test creating a tax liability."""
        liability = TaxLiability.objects.create(
            organization=self.organization,
            financial_period=self.period,
            tax_type="VAT",
            total_revenue=Decimal("10000.00"),
            total_tax_collected=Decimal("1500.00"),
            due_date=date(2024, 2, 14),
        )
        self.assertEqual(liability.tax_type, "VAT")
        self.assertEqual(liability.total_tax_collected, Decimal("1500.00"))
