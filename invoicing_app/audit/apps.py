from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'invoicing_app.audit'
    verbose_name = 'Audit & Compliance'

    def ready(self):
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
