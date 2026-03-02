# invoicing_app package

__version__ = "3.0.0"
__version_name__ = "Enterprise Intelligence"
__api_version__ = "v2.0"

# Celery setup - ensure Celery app is loaded on Django startup
from .celery import app as celery_app

__all__ = ('celery_app',)

