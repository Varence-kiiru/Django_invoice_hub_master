"""Deliveries app configuration."""
from django.apps import AppConfig


class DeliveriesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'invoicing_app.deliveries'
    verbose_name = 'Deliveries'
    
    def ready(self):
        """Import signals when app is ready."""
        import invoicing_app.deliveries.signals
