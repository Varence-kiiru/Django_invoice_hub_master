from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "invoicing_app.products"
    verbose_name = "Products"

    def ready(self):
        # Import signals to register handlers
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
