"""Development settings: opinionated defaults for local development.

These settings are permissive by design (e.g., `DEBUG = True`) but still
demonstrate recommended configuration surfaces. Keep secrets in `.env`.
"""

from .base import *  # noqa: F401,F403

# Development convenience
DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]

# Disable security middleware in development
SECURITY_MIDDLEWARE_ENABLED = False

# Remove security middleware from the middleware stack
MIDDLEWARE = [
    m
    for m in MIDDLEWARE
    if m
    not in (
        "invoicing_app.organizations.security.RateLimitMiddleware",
        "invoicing_app.organizations.security.SecurityHeadersMiddleware",
        "invoicing_app.organizations.security.CSPMiddleware",
    )
]

# Database: prefer env-configured MySQL, fallback to SQLite for quick setup
if get_env("MYSQL_DATABASE"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": get_env("MYSQL_DATABASE"),
            "USER": get_env("MYSQL_USER", "root"),
            "PASSWORD": get_env("MYSQL_PASSWORD", ""),
            "HOST": get_env("MYSQL_HOST", "127.0.0.1"),
            "PORT": get_env("MYSQL_PORT", "3306"),
            "OPTIONS": {"init_command": "SET sql_mode='STRICT_TRANS_TABLES'"},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(BASE_DIR / "db.sqlite3"),
        }
    }


# CORS for frontend dev (comma-separated env var or single origin)
CORS_ALLOWED_ORIGINS = (
    get_env("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if get_env("CORS_ALLOWED_ORIGINS", None)
    else ["http://localhost:3000"]
)

# Email: console backend is handy in development
EMAIL_BACKEND = get_env(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)

# Static/media served from disk in development
STATICFILES_DIRS = [BASE_DIR / "static"]

# Use local file storage in development instead of S3
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"
