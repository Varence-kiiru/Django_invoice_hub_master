from django.test import TestCase, Client as DjangoClient
from django.urls import reverse
from django.contrib.auth.models import User


class HtmlViewsTest(TestCase):
    def setUp(self):
        self.client = DjangoClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="pass12345",  # pragma: allowlist secret
        )

    def test_login_page_get(self):
        resp = self.client.get(reverse("organizations:login"))
        self.assertEqual(resp.status_code, 200)

    def test_login_post_invalid(self):
        resp = self.client.post(
            reverse("organizations:login"),
            {"email": "nope@example.com", "password": "x"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Invalid email or password", status_code=200)

    def test_dashboard_requires_login(self):
        resp = self.client.get(reverse("core:dashboard"))
        self.assertEqual(resp.status_code, 302)  # redirect to login

    def test_dashboard_authenticated(self):
        self.client.login(
            username="testuser", password="pass12345"
        )  # pragma: allowlist secret
        resp = self.client.get(reverse("core:dashboard"))
        self.assertEqual(resp.status_code, 200)

    def test_can_view_financials_helper_exists(self):
        import invoicing_app.core.permissions as permissions

        self.assertTrue(hasattr(permissions, "can_view_financials"))
        self.assertFalse(permissions.can_view_financials(self.user))
