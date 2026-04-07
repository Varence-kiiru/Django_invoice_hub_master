"""ASGI entrypoint for invoicing_app."""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "invoicing_app.settings.development")

application = get_asgi_application()
