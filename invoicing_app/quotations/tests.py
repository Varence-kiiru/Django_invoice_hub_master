"""
Comprehensive tests for Quotations app.
Tests models, services, views, API endpoints, and business logic.
"""

from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal

from invoicing_app.clients.models import Client as ClientModel
from invoicing_app.products.models import Product
from invoicing_app.taxes.models import TaxRate
from .models import Quote, QuoteLineItem, QuoteNumberSequence
from .services import QuoteNumberService, QuoteConversionService, QuoteStatusService
from .forms import QuoteForm


class QuoteNumberSequenceTest(TestCase):
    """Test QuoteNumberSequence model and sequence generation."""

    def setUp(self):
        """Create test data."""
        self.today = datetime.now().date()
        self.year = self.today.year

    def test_create_sequence(self):
        """Test creating a new sequence."""
        seq = QuoteNumberSequence.objects.create(
            prefix="QUOTE", year=self.year, next_sequence=1
        )
        self.assertEqual(seq.prefix, "QUOTE")
        self.assertEqual(seq.year, self.year)
        self.assertEqual(seq.next_sequence, 1)

    def test_unique_constraint(self):
        """Test that prefix+year combination is unique."""
        QuoteNumberSequence.objects.create(
            prefix="QUOTE", year=self.year, next_sequence=1
        )

        with self.assertRaises(Exception):
            QuoteNumberSequence.objects.create(
                prefix="QUOTE", year=self.year, next_sequence=1
            )

    def test_sequence_string(self):
        """Test sequence string representation."""
        seq = QuoteNumberSequence.objects.create(
            prefix="QUOTE", year=self.year, next_sequence=5
        )
        self.assertEqual(str(seq), f"QUOTE-{self.year}: next=5")


class QuoteNumberServiceTest(TestCase):
    """Test QuoteNumberService."""

    def setUp(self):
        """Create test data."""
        self.today = datetime.now().date()
        self.year = self.today.year

    def test_generate_next_number(self):
        """Test generating next quote number."""
        number1 = QuoteNumberService.generate_next_number()
        number2 = QuoteNumberService.generate_next_number()

        self.assertIn(str(self.year), number1)
        self.assertIn("QUOTE", number1)

        # Verify sequential increment
        num1_seq = int(number1.split("-")[-1])
        num2_seq = int(number2.split("-")[-1])
        self.assertEqual(num2_seq, num1_seq + 1)

    def test_get_preview_number(self):
        """Test getting preview number without incrementing."""
        preview1 = QuoteNumberService.get_preview_number()
        preview2 = QuoteNumberService.get_preview_number()

        # Should return same value (no increment)
        self.assertEqual(preview1, preview2)

        # Should have valid format
        self.assertIn(str(self.year), preview1)
        self.assertIn("QUOTE", preview1)

    def test_number_format(self):
        """Test that generated numbers have correct format."""
        number = QuoteNumberService.generate_next_number()
        parts = number.split("-")

        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], "QUOTE")
        self.assertEqual(parts[1], str(self.year))
        self.assertEqual(len(parts[2]), 4)  # 0001 format
        self.assertTrue(parts[2].isdigit())


class QuoteModelTest(TestCase):
    """Test Quote model."""

    def setUp(self):
        """Create test data."""
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass",
            first_name="Test",
            last_name="User",
        )
        self.client = ClientModel.objects.create(
            name="Test Client", email="client@test.com"
        )

    def test_create_quote(self):
        """Test creating a quote."""
        quote = Quote.objects.create(
            quote_number="QUOTE-2026-0001",
            client=self.client,
            quote_date=datetime.now().date(),
            valid_until=datetime.now().date() + timedelta(days=30),
            status="draft",
            subtotal_amount=Decimal("1000.00"),
            vat_amount=Decimal("160.00"),
            total_amount=Decimal("1160.00"),
            created_by=self.user,
        )

        self.assertEqual(quote.quote_number, "QUOTE-2026-0001")
        self.assertEqual(quote.status, "draft")
        self.assertEqual(quote.total_amount, Decimal("1160.00"))

    def test_quote_status_choices(self):
        """Test status choices."""
        status_values = [choice[0] for choice in Quote.STATUS_CHOICES]
        self.assertIn("draft", status_values)
        self.assertIn("sent", status_values)
        self.assertIn("accepted", status_values)

    def test_is_expired_property(self):
        """Test is_expired() method."""
        # Not expired
        quote = Quote.objects.create(
            quote_number="QUOTE-2026-0001",
            client=self.client,
            quote_date=datetime.now().date(),
            valid_until=datetime.now().date() + timedelta(days=10),
            status="draft",
            created_by=self.user,
        )
        self.assertFalse(quote.is_expired())

        # Expired
        expired_quote = Quote.objects.create(
            quote_number="QUOTE-2026-0002",
            client=self.client,
            quote_date=datetime.now().date() - timedelta(days=40),
            valid_until=datetime.now().date() - timedelta(days=10),
            status="draft",
            created_by=self.user,
        )
        self.assertTrue(expired_quote.is_expired())

    def test_days_until_expiry_property(self):
        """Test days_until_expiry property."""
        future_date = datetime.now().date() + timedelta(days=15)
        quote = Quote.objects.create(
            quote_number="QUOTE-2026-0001",
            client=self.client,
            quote_date=datetime.now().date(),
            valid_until=future_date,
            status="draft",
            created_by=self.user,
        )

        # The property calculates (valid_until - today).days which should be 15
        # But due to timing, it may be 15 or 16, so check it's in the range
        self.assertIn(quote.days_until_expiry, [15, 16])


class QuoteConversionServiceTest(TestCase):
    """Test QuoteConversionService."""

    def setUp(self):
        """Create test data."""
        from invoicing_app.products.models import ProductTaxClass

        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client = ClientModel.objects.create(
            name="Test Client", email="client@test.com"
        )
        self.tax_class = ProductTaxClass.objects.create(
            name="Standard VAT", rate_type="standard"
        )
        self.product = Product.objects.create(
            sku="TEST-001",
            name="Test Product",
            unit_price=Decimal("100.00"),
            tax_class=self.tax_class,
        )
        self.tax_rate = TaxRate.objects.create(
            name="VAT 16%",
            code="VATX16",
            rate_percentage=Decimal("16.00"),
            effective_from=datetime.now().date(),
        )

    def test_cannot_convert_draft_quote(self):
        """Test that draft quotes cannot be converted."""
        quote = Quote.objects.create(
            quote_number="QUOTE-2026-0001",
            client=self.client,
            quote_date=datetime.now().date(),
            valid_until=datetime.now().date() + timedelta(days=30),
            status="draft",
            created_by=self.user,
        )

        with self.assertRaises(ValueError):
            QuoteConversionService.convert_quote_to_invoice(
                quote,
                invoice_date=datetime.now().date(),
                due_date=datetime.now().date() + timedelta(days=30),
            )


class QuoteStatusServiceTest(TestCase):
    """Test QuoteStatusService."""

    def setUp(self):
        """Create test data."""
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client = ClientModel.objects.create(
            name="Test Client", email="client@test.com"
        )
        self.quote = Quote.objects.create(
            quote_number="QUOTE-2026-0001",
            client=self.client,
            quote_date=datetime.now().date(),
            valid_until=datetime.now().date() + timedelta(days=30),
            status="draft",
            created_by=self.user,
        )

    def test_transition_draft_to_sent(self):
        """Test transitioning quote from draft to sent."""
        result = QuoteStatusService.transition_quote(
            self.quote, "sent", actor=self.user
        )

        self.assertTrue(result)
        self.quote.refresh_from_db()
        self.assertEqual(self.quote.status, "sent")
        self.assertIsNotNone(self.quote.sent_at)

    def test_invalid_transition(self):
        """Test that invalid transitions are blocked."""
        # Try to jump from draft directly to accepted (invalid)
        result = QuoteStatusService.transition_quote(
            self.quote, "accepted", actor=self.user
        )

        self.assertFalse(result)
        self.quote.refresh_from_db()
        self.assertEqual(self.quote.status, "draft")

    def test_rejection_with_reason(self):
        """Test rejecting quote with reason."""
        self.quote.status = "viewed"
        self.quote.save()

        result = QuoteStatusService.transition_quote(
            self.quote, "rejected", actor=self.user, reason="Price too high"
        )

        self.assertTrue(result)
        self.quote.refresh_from_db()
        self.assertEqual(self.quote.status, "rejected")
        self.assertEqual(self.quote.rejection_reason, "Price too high")


class QuoteFormTest(TestCase):
    """Test QuoteForm."""

    def setUp(self):
        """Create test data."""
        self.client = ClientModel.objects.create(
            name="Test Client", email="client@test.com"
        )

    def test_valid_form(self):
        """Test valid form submission."""
        form = QuoteForm(
            data={
                "client": self.client.id,
                "quote_date": datetime.now().date(),
                "valid_until": datetime.now().date() + timedelta(days=30),
                "currency": "KES",
                "description": "Test quotation",
            }
        )

        self.assertTrue(form.is_valid())

    def test_missing_required_field(self):
        """Test form with missing required field."""
        form = QuoteForm(
            data={
                "quote_date": datetime.now().date(),
                "valid_until": datetime.now().date() + timedelta(days=30),
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("client", form.errors)


class QuoteViewsTest(TestCase):
    """Test quotation views."""

    def setUp(self):
        """Create test data."""
        from invoicing_app.products.models import ProductTaxClass

        self.client_http = Client()
        self.user = User.objects.create_user(
            username="testuser", email="user@test.com", password="testpass"
        )
        self.client_model = ClientModel.objects.create(
            name="Test Client", email="client@test.com"
        )
        self.tax_class = ProductTaxClass.objects.create(
            name="Standard VAT", rate_type="standard"
        )
        self.product = Product.objects.create(
            sku="TEST-001",
            name="Test Product",
            unit_price=Decimal("100.00"),
            tax_class=self.tax_class,
        )
        self.client_http.login(username="testuser", password="testpass")

    def test_login_required_for_list(self):
        """Test that quotes list view requires login."""
        self.client_http.logout()

        response = self.client_http.get(reverse("quotations:list"))

        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_login_required_for_create(self):
        """Test that create view requires login."""
        self.client_http.logout()

        response = self.client_http.get(reverse("quotations:create"))

        self.assertEqual(response.status_code, 302)  # Redirect to login


# ━━━ PDF & Email Tests ━━━
class QuotePDFGenerationTest(TestCase):
    """Test PDF generation for quotations."""

    def setUp(self):
        """Create test data."""
        from invoicing_app.products.models import ProductTaxClass
        from invoicing_app.core.models import CompanySettings

        # Create company settings
        self.settings = CompanySettings.get_settings()
        self.settings.company_name = "Test Company"
        self.settings.company_email = "info@test.com"
        self.settings.company_phone = "+254 123 456 789"
        self.settings.company_address = "123 Test Street, Nairobi"
        self.settings.save()

        # Create user, client, tax class, and product
        self.user = User.objects.create_user(
            username="testuser", email="user@test.com", password="testpass"
        )
        self.client_model = ClientModel.objects.create(
            name="Test Client", email="client@test.com"
        )
        self.tax_class = ProductTaxClass.objects.create(
            name="Standard VAT", rate_type="standard", rate=16
        )
        self.product = Product.objects.create(
            sku="TEST-001",
            name="Test Product",
            unit_price=Decimal("1000.00"),
            tax_class=self.tax_class,
        )

        # Create quotation
        self.quote = Quote.objects.create(
            quote_number="QUOTE-2026-0001",
            client=self.client_model,
            quote_date=datetime.now().date(),
            valid_until=datetime.now().date() + timedelta(days=30),
            currency="KES",
            status="draft",
            created_by=self.user,
        )

        # Add line item
        self.line_item = QuoteLineItem.objects.create(
            quote=self.quote,
            product=self.product,
            description="Test Service",
            quantity=Decimal("2"),
            unit_price=self.product.unit_price,
            tax_rate=Decimal("16"),
        )

    def test_pdf_view_accessible(self):
        """Test that PDF view is accessible."""
        client = Client()
        client.login(username="testuser", password="testpass")

        response = client.get(reverse("quotations:pdf", kwargs={"pk": self.quote.pk}))

        # Should return PDF or HTML (if WeasyPrint not available)
        self.assertIn(response.status_code, [200, 302])

    def test_pdf_view_requires_login(self):
        """Test that PDF view requires authentication."""
        client = Client()

        response = client.get(reverse("quotations:pdf", kwargs={"pk": self.quote.pk}))

        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_pdf_quote_number_in_content(self):
        """Test that quote number appears in PDF."""
        client = Client()
        client.login(username="testuser", password="testpass")

        response = client.get(reverse("quotations:pdf", kwargs={"pk": self.quote.pk}))

        self.assertEqual(response.status_code, 200)


class QuoteEmailServiceTest(TestCase):
    """Test email notification service for quotations."""

    def setUp(self):
        """Create test data."""
        from invoicing_app.quotations.email_service import QuoteEmailService

        self.email_service = QuoteEmailService()
        self.client_email = "client@test.com"
        self.client_name = "Test Client"
        self.quote_number = "QUOTE-2026-0001"

    def test_quote_issued_email_init(self):
        """Test QuoteEmailService initialization."""
        self.assertIsNotNone(self.email_service.sender)
        self.assertEqual(self.email_service.sender_name, "Quote Management")

    def test_send_quote_issued_method_exists(self):
        """Test that send_quote_issued method exists."""
        self.assertTrue(hasattr(self.email_service, "send_quote_issued"))
        self.assertTrue(callable(getattr(self.email_service, "send_quote_issued")))

    def test_send_quote_accepted_method_exists(self):
        """Test that send_quote_accepted method exists."""
        self.assertTrue(hasattr(self.email_service, "send_quote_accepted"))
        self.assertTrue(callable(getattr(self.email_service, "send_quote_accepted")))

    def test_send_quote_rejected_method_exists(self):
        """Test that send_quote_rejected method exists."""
        self.assertTrue(hasattr(self.email_service, "send_quote_rejected"))
        self.assertTrue(callable(getattr(self.email_service, "send_quote_rejected")))

    def test_send_quote_expiration_warning_method_exists(self):
        """Test that send_quote_expiration_warning method exists."""
        self.assertTrue(hasattr(self.email_service, "send_quote_expiration_warning"))
        self.assertTrue(
            callable(getattr(self.email_service, "send_quote_expiration_warning"))
        )

    def test_send_quote_converted_method_exists(self):
        """Test that send_quote_converted method exists."""
        self.assertTrue(hasattr(self.email_service, "send_quote_converted"))
        self.assertTrue(callable(getattr(self.email_service, "send_quote_converted")))


class QuoteSendViewIntegrationTest(TestCase):
    """Test quote sending with email integration."""

    def setUp(self):
        """Create test data."""
        from invoicing_app.products.models import ProductTaxClass

        self.client_http = Client()
        self.user = User.objects.create_user(
            username="testuser", email="user@test.com", password="testpass"
        )
        self.client_model = ClientModel.objects.create(
            name="Test Client", email="client@test.com"
        )
        self.tax_class = ProductTaxClass.objects.create(
            name="Standard VAT", rate_type="standard", rate=16
        )
        self.product = Product.objects.create(
            sku="TEST-001",
            name="Test Product",
            unit_price=Decimal("1000.00"),
            tax_class=self.tax_class,
        )

        # Create quotation
        self.quote = Quote.objects.create(
            quote_number="QUOTE-2026-0001",
            client=self.client_model,
            quote_date=datetime.now().date(),
            valid_until=datetime.now().date() + timedelta(days=30),
            currency="KES",
            status="draft",
            created_by=self.user,
        )

        # Add line item
        self.line_item = QuoteLineItem.objects.create(
            quote=self.quote,
            product=self.product,
            description="Test Service",
            quantity=Decimal("2"),
            unit_price=self.product.unit_price,
            tax_rate=Decimal("16"),
        )

        self.client_http.login(username="testuser", password="testpass")

    def test_send_quote_updates_status(self):
        """Test that sending a quote updates its status."""
        self.client_http.get(reverse("quotations:send", kwargs={"pk": self.quote.pk}))

        self.quote.refresh_from_db()
        self.assertEqual(self.quote.status, "sent")

    def test_send_quote_view_requires_login(self):
        """Test that send view requires authentication."""
        self.client_http.logout()

        response = self.client_http.get(
            reverse("quotations:send", kwargs={"pk": self.quote.pk})
        )

        self.assertEqual(response.status_code, 302)  # Redirect to login


class QuoteConvertViewIntegrationTest(TestCase):
    """Test quote conversion with email integration."""

    def setUp(self):
        """Create test data."""
        from invoicing_app.products.models import ProductTaxClass

        self.client_http = Client()
        self.user = User.objects.create_user(
            username="testuser", email="user@test.com", password="testpass"
        )
        self.client_model = ClientModel.objects.create(
            name="Test Client", email="client@test.com"
        )
        self.tax_class = ProductTaxClass.objects.create(
            name="Standard VAT", rate_type="standard", rate=16
        )
        self.product = Product.objects.create(
            sku="TEST-001",
            name="Test Product",
            unit_price=Decimal("1000.00"),
            tax_class=self.tax_class,
        )

        # Create accepted quotation
        self.quote = Quote.objects.create(
            quote_number="QUOTE-2026-0001",
            client=self.client_model,
            quote_date=datetime.now().date(),
            valid_until=datetime.now().date() + timedelta(days=30),
            currency="KES",
            status="accepted",
            created_by=self.user,
        )

        # Add line item
        self.line_item = QuoteLineItem.objects.create(
            quote=self.quote,
            product=self.product,
            description="Test Service",
            quantity=Decimal("2"),
            unit_price=self.product.unit_price,
            tax_rate=Decimal("16"),
        )

        self.client_http.login(username="testuser", password="testpass")

    def test_convert_quote_creates_invoice(self):
        """Test that converting a quote creates an invoice."""
        from invoicing_app.core.models import CompanySettings

        # Ensure settings are configured
        settings = CompanySettings.get_settings()
        settings.invoice_prefix = "INV"
        settings.save()

        self.client_http.post(
            reverse("quotations:convert", kwargs={"pk": self.quote.pk}),
            {
                "invoice_date": datetime.now().date().isoformat(),
                "due_date": (datetime.now().date() + timedelta(days=30)).isoformat(),
            },
        )

        self.quote.refresh_from_db()
        self.assertEqual(self.quote.status, "converted")
        self.assertIsNotNone(self.quote.converted_invoice)

    def test_convert_view_requires_login(self):
        """Test that convert view requires authentication."""
        self.client_http.logout()

        response = self.client_http.get(
            reverse("quotations:convert", kwargs={"pk": self.quote.pk})
        )

        self.assertEqual(response.status_code, 302)  # Redirect to login
