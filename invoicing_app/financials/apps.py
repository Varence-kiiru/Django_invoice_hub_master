from django.apps import AppConfig


class FinancialsConfig(AppConfig):
    """Financial tracking app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "invoicing_app.financials"
    verbose_name = "Financial Tracking"

    def ready(self):
        """Import signals when app is ready."""
        from . import signals  # noqa: F401
