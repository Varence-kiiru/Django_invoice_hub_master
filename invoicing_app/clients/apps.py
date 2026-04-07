from django.apps import AppConfig


class ClientsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "invoicing_app.clients"
    verbose_name = "Clients"

    def ready(self):
        # Import signals to register handlers
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
