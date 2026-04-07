"""WSGI entrypoint for invoicing_app."""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "invoicing_app.settings.production")

application = get_wsgi_application()
