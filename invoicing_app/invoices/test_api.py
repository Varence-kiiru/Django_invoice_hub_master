"""
Integration tests for Invoice Management API endpoints.
Tests complete workflows and API interactions.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from invoicing_app.clients.models import Client
from invoicing_app.invoices.models import Invoice, InvoiceLineItem
from invoicing_app.payments.models import Payment, PaymentMethod
from invoicing_app.taxes.models import TaxRate


class APIAuthenticationTestCase(TestCase):
    """Test API authentication and authorization."""

    def setUp(self):
        """Set up test fixtures."""
        self.client_api = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",  # pragma: allowlist secret
            email="test@example.com",
        )

    def test_api_requires_authentication(self):
        """Test that API endpoints require authentication."""
        response = self.client_api.get("/api/clients/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_api_jwt_token_authentication(self):
        """Test JWT token authentication."""
        refresh = RefreshToken.for_user(self.user)
        self.client_api.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = self.client_api.get("/api/clients/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_api_invalid_token(self):
        """Test that invalid token is rejected."""
        self.client_api.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")
        response = self.client_api.get("/api/clients/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ClientAPITestCase(TestCase):
    """Test Client API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client_api = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",  # pragma: allowlist secret
        )
        refresh = RefreshToken.for_user(self.user)
        self.client_api.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_list_clients(self):
        """Test listing clients."""
        Client.objects.create(
            name="Client 1",
            email="client1@example.com",
            phone="1111111111",
            tax_id="P000000001A",
        )
        Client.objects.create(
            name="Client 2",
            email="client2@example.com",
            phone="2222222222",
            tax_id="P000000002A",
        )

        response = self.client_api.get("/api/clients/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 2)

    def test_create_client(self):
        """Test creating a client."""
        data = {
            "name": "New Client",
            "email": "new@example.com",
            "phone": "3333333333",
            "tax_id": "P000000003A",
            "currency": "KES",
            "payment_terms": 30,
        }

        response = self.client_api.post("/api/clients/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Client")

    def test_retrieve_client(self):
        """Test retrieving a single client."""
        client = Client.objects.create(
            name="Test Client",
            email="test@example.com",
            phone="4444444444",
            tax_id="P000000004A",
        )

        response = self.client_api.get(f"/api/clients/{client.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Client")

    def test_update_client(self):
        """Test updating a client."""
        client = Client.objects.create(
            name="Test Client",
            email="test@example.com",
            phone="4444444444",
            tax_id="P000000004A",
        )

        data = {"name": "Updated Client"}
        response = self.client_api.patch(f"/api/clients/{client.id}/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Client")

    def test_delete_client(self):
        """Test deleting a client."""
        client = Client.objects.create(
            name="Test Client",
            email="test@example.com",
            phone="4444444444",
            tax_id="P000000004A",
        )

        response = self.client_api.delete(f"/api/clients/{client.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify deletion
        response = self.client_api.get(f"/api/clients/{client.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class InvoiceAPITestCase(TestCase):
    """Test Invoice API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client_api = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",  # pragma: allowlist secret
        )
        refresh = RefreshToken.for_user(self.user)
        self.client_api.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        # Create test client
        self.client = Client.objects.create(
            name="Test Client",
            email="test@example.com",
            phone="1234567890",
            tax_id="P000000001A",
        )

        # Create test tax rate
        self.tax_rate = TaxRate.objects.create(
            name="Standard VAT",
            rate_percentage=16,
            is_vat_applicable=True,
            effective_from=timezone.now().date(),
        )

    def test_create_draft_invoice(self):
        """Test creating a draft invoice."""
        data = {
            "client": self.client.id,
            "invoice_date": timezone.now().date().isoformat(),
            "due_date": (
                timezone.now().date() + timezone.timedelta(days=30)
            ).isoformat(),
            "currency": "KES",
            "status": "draft",
        }

        response = self.client_api.post("/api/invoices/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "draft")

    def test_list_invoices(self):
        """Test listing invoices."""
        Invoice.objects.create(
            invoice_number="INV-2026-0001",
            client=self.client,
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date() + timezone.timedelta(days=30),
            currency="KES",
            status="draft",
        )

        response = self.client_api.get("/api/invoices/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_invoice_line_items(self):
        """Test adding line items to invoice."""
        invoice = Invoice.objects.create(
            invoice_number="INV-2026-0001",
            client=self.client,
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date() + timezone.timedelta(days=30),
            currency="KES",
            status="draft",
        )

        line_item_data = {
            "invoice": invoice.id,
            "description": "Test Service",
            "quantity": "1.00",
            "unit_price": "1000.00",
            "line_amount": "1000.00",
            "tax_rate": self.tax_rate.id,
            "tax_amount": "160.00",
            "line_total": "1160.00",
        }

        response = self.client_api.post("/api/invoice-line-items/", line_item_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify invoice totals updated
        invoice.refresh_from_db()
        self.assertEqual(invoice.subtotal_amount, Decimal("1000.00"))
        self.assertEqual(invoice.vat_amount, Decimal("160.00"))
        self.assertEqual(invoice.total_amount, Decimal("1160.00"))

    def test_issue_invoice(self):
        """Test issuing an invoice."""
        invoice = Invoice.objects.create(
            invoice_number="INV-2026-0001",
            client=self.client,
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date() + timezone.timedelta(days=30),
            currency="KES",
            status="draft",
            subtotal_amount=Decimal("1000.00"),
            vat_amount=Decimal("160.00"),
            total_amount=Decimal("1160.00"),
        )

        # Add line item
        InvoiceLineItem.objects.create(
            invoice=invoice,
            description="Test Service",
            quantity=Decimal("1"),
            unit_price=Decimal("1000.00"),
            line_amount=Decimal("1000.00"),
            tax_rate=self.tax_rate,
            tax_amount=Decimal("160.00"),
            line_total=Decimal("1160.00"),
        )

        # Issue invoice
        data = {"status": "issued"}
        response = self.client_api.patch(f"/api/invoices/{invoice.id}/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "issued")

        # Verify snapshot created
        from invoicing_app.audit.models import InvoiceSnapshot

        snapshot = InvoiceSnapshot.objects.filter(invoice=invoice).first()
        self.assertIsNotNone(snapshot)


class PaymentAPITestCase(TestCase):
    """Test Payment API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client_api = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",  # pragma: allowlist secret
        )
        refresh = RefreshToken.for_user(self.user)
        self.client_api.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        # Create test invoice
        self.client = Client.objects.create(
            name="Test Client",
            email="test@example.com",
            phone="1234567890",
            tax_id="P000000001A",
        )

        self.invoice = Invoice.objects.create(
            invoice_number="INV-2026-0001",
            client=self.client,
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date() + timezone.timedelta(days=30),
            currency="KES",
            status="issued",
            total_amount=Decimal("1160.00"),
        )

        # Create payment method
        self.payment_method = PaymentMethod.objects.create(name="Bank Transfer")

    def test_record_payment(self):
        """Test recording a payment."""
        data = {
            "invoice": self.invoice.id,
            "amount": "580.00",
            "payment_method": self.payment_method.id,
            "payment_date": timezone.now().date().isoformat(),
            "status": "pending",
        }

        response = self.client_api.post("/api/payments/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_confirm_payment(self):
        """Test confirming a payment."""
        payment = Payment.objects.create(
            invoice=self.invoice,
            amount=Decimal("580.00"),
            payment_method=self.payment_method,
            payment_date=timezone.now().date(),
            status="pending",
        )

        data = {"status": "confirmed"}
        response = self.client_api.patch(f"/api/payments/{payment.id}/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify invoice amounts updated
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amount_paid, Decimal("580.00"))
        self.assertEqual(self.invoice.amount_due, Decimal("580.00"))

    def test_full_payment(self):
        """Test full payment of invoice."""
        # Create and confirm payment
        payment = Payment.objects.create(
            invoice=self.invoice,
            amount=Decimal("1160.00"),
            payment_method=self.payment_method,
            payment_date=timezone.now().date(),
            status="pending",
        )

        data = {"status": "confirmed"}
        response = self.client_api.patch(f"/api/payments/{payment.id}/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify invoice marked as paid
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amount_due, Decimal("0.00"))
        self.assertEqual(self.invoice.status, "paid")


class ErrorHandlingAPITestCase(TestCase):
    """Test error handling in API responses."""

    def setUp(self):
        """Set up test fixtures."""
        self.client_api = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )
        refresh = RefreshToken.for_user(self.user)
        self.client_api.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_invalid_client_data(self):
        """Test validation errors on invalid client data."""
        data = {
            "name": "Invalid Client",
            "email": "invalid-email",  # Invalid email format
            "phone": "1234567890",
            "tax_id": "P000000001A",
        }

        response = self.client_api.post("/api/clients/", data)
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST])

    def test_404_not_found(self):
        """Test 404 response for non-existent resource."""
        response = self.client_api.get("/api/clients/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_pagination(self):
        """Test pagination in list endpoints."""
        # Create multiple clients
        for i in range(30):
            Client.objects.create(
                name=f"Client {i}",
                email=f"client{i}@example.com",
                phone=f"{i:010d}",
                tax_id=f"P{i:09d}A",
            )

        response = self.client_api.get("/api/clients/?limit=10")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data["results"]), 10)
        self.assertIsNotNone(response.data.get("next"))

    def test_filtering(self):
        """Test filtering in list endpoints."""
        Client.objects.create(
            name="Active Client",
            email="active@example.com",
            phone="1111111111",
            tax_id="P000000001A",
            is_active=True,
        )
        Client.objects.create(
            name="Inactive Client",
            email="inactive@example.com",
            phone="2222222222",
            tax_id="P000000002A",
            is_active=False,
        )

        response = self.client_api.get("/api/clients/?is_active=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only include active clients

    def test_search(self):
        """Test search functionality in list endpoints."""
        Client.objects.create(
            name="John Doe Ltd",
            email="john@example.com",
            phone="1234567890",
            tax_id="P000000001A",
        )

        response = self.client_api.get("/api/clients/?search=John")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should find clients matching 'John'
