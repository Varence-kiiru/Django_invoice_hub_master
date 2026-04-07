# invoicing_app package

__version__ = "4.5.0"
__version_name__ = "Complete Financial Intelligence"
__api_version__ = "v2.1"

# Celery setup - ensure Celery app is loaded on Django startup
from .celery import app as celery_app

__all__ = ("celery_app",)
