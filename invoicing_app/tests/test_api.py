from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from invoicing_app.clients.models import Client


class ApiTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="apiuser",
            email="api@example.com",
            password="secret123",  # pragma: allowlist secret
        )
        self.client = APIClient()

    def obtain_token(self):
        resp = self.client.post(
            "/api/v1/token/",
            {
                "username": "apiuser",
                "password": "secret123",
            },  # pragma: allowlist secret
            format="json",
        )
        return resp.json().get("access")

    def test_clients_endpoint_requires_auth(self):
        resp = self.client.get("/api/v1/clients/")
        self.assertEqual(resp.status_code, 401)

    def test_clients_list_with_token(self):
        token = self.obtain_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        # create a client record
        Client.objects.create(name="ACME Ltd", tax_id="TAX123")
        resp = self.client.get("/api/v1/clients/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(isinstance(data, list) or data.get("results") is not None)
