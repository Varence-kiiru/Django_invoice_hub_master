from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "invoicing_app.payments"
    verbose_name = "Payments"

    def ready(self):
        # Import signals to register handlers
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
