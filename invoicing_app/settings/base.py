
"""Production-minded base Django settings.

This file is intentionally conservative and environment-driven. It exposes
well-documented options for logging, security, storage, email, caching,
and third-party integrations. Environment variables are the authority.
"""

from __future__ import annotations

import os
from pathlib import Path
from datetime import timedelta
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment helpers if available (django-environ optional)
try:
    import environ

    env = environ.Env()
    # read .env file if present (development convenience)
    environ.Env.read_env(BASE_DIR / ".env")
except Exception:  # pragma: no cover - optional runtime
    env = None


def get_env(key: str, default: Any = None) -> Any:
    if env is not None:
        return env(key, default=default)
    return os.environ.get(key, default)


# Core
SECRET_KEY = get_env("DJANGO_SECRET_KEY", "replace-me-local")
DEBUG = False

ALLOWED_HOSTS = get_env("DJANGO_ALLOWED_HOSTS", "").split(",") if get_env("DJANGO_ALLOWED_HOSTS", "") else []

# Applications
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "corsheaders",
    "django_filters",
    "anymail",
    "storages",
    "django_celery_beat",
    "django_celery_results",

    # Invoicing App Modules
    "invoicing_app.core.apps.CoreConfig",
    "invoicing_app.organizations.apps.OrganizationsConfig",
    "invoicing_app.user_management.apps.UserManagementConfig",
    "invoicing_app.clients.apps.ClientsConfig",
    "invoicing_app.products.apps.ProductsConfig",
    "invoicing_app.invoices.apps.InvoicesConfig",
    "invoicing_app.taxes.apps.TaxesConfig",
    "invoicing_app.payments.apps.PaymentsConfig",
    "invoicing_app.quotations.apps.QuotationsConfig",
    "invoicing_app.deliveries.apps.DeliveriesConfig",
    "invoicing_app.audit.apps.AuditConfig",
    "invoicing_app.notifications.apps.NotificationsConfig",
    "invoicing_app.expenses.apps.ExpensesConfig",
]

# Conditionals: add if available to avoid hard dependency during bootstrap
for optional_app in ("drf_spectacular", "drf_spectacular_sidecar"):
    try:
        __import__(optional_app)
    except Exception:
        pass
    else:
        INSTALLED_APPS.append(optional_app)


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "invoicing_app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(BASE_DIR / "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "invoicing_app.core.context_processors.company_settings",
                "invoicing_app.core.context_processors.user_permissions",
                "invoicing_app.core.context_processors.app_version",
            ],
        },
    },
]

WSGI_APPLICATION = "invoicing_app.wsgi.application"

# Database is intentionally left to environment-specific settings

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Authentication & REST framework
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

REST_FRAMEWORK = {
    # Authentication
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    
    # Permissions
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    
    # Filtering & Search
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    
    # Pagination Configuration
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": int(get_env("DRF_PAGE_SIZE", 25)),
    
    # Pagination Limits
    "MAX_PAGE_SIZE": int(get_env("DRF_MAX_PAGE_SIZE", 1000)),
    "COUNT_TIMEOUT": 5,  # Cache count for performance
    
    # Error Handling
    "EXCEPTION_HANDLER": "invoicing_app.core.exception_handlers.custom_exception_handler",
    
    # Response Formatting
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    
    # Versioning (optional, for API evolution)
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    
    # Throttling (rate limiting per user/IP)
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
    },
    
    # Schema
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# Simple JWT sensible defaults
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(get_env("JWT_ACCESS_MINUTES", 15))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(get_env("JWT_REFRESH_DAYS", 7))),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
}


# Internationalization
LANGUAGE_CODE = get_env("LANGUAGE_CODE", "en-us")
TIME_ZONE = get_env("TIME_ZONE", "Africa/Nairobi")
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static and media
STATIC_URL = "/static/"
STATIC_ROOT = str(BASE_DIR / "staticfiles")
MEDIA_URL = "/media/"
MEDIA_ROOT = str(BASE_DIR / "media")

# Storage backends (S3 via django-storages) - enabled when env present
if get_env("AWS_S3_BUCKET_NAME"):
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_S3_REGION_NAME = get_env("AWS_S3_REGION_NAME", "")
    AWS_ACCESS_KEY_ID = get_env("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = get_env("AWS_SECRET_ACCESS_KEY", "")
    AWS_S3_BUCKET_NAME = get_env("AWS_S3_BUCKET_NAME")


# Email configuration (Anymail adapters)
EMAIL_BACKEND = "invoicing_app.core.email_backend.DynamicEmailBackend"
EMAIL_HOST = get_env("EMAIL_HOST", "localhost")
EMAIL_PORT = int(get_env("EMAIL_PORT", 25))
EMAIL_HOST_USER = get_env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = get_env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = get_env("EMAIL_USE_TLS", "False").lower() in ("1", "true", "yes")
DEFAULT_FROM_EMAIL = get_env("DEFAULT_FROM_EMAIL", "webmaster@localhost")

ANYPAYLOAD = {}
if get_env("ANYMAIL_API_KEY"):
    # Example placeholder for anymail provider
    ANYMAIL = {"SENDGRID_API_KEY": get_env("ANYMAIL_API_KEY")}


# Caching (Redis recommended)
if get_env("REDIS_URL"):
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": get_env("REDIS_URL"),
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        }
    }
else:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}


# Celery settings (optional) - useful hints
CELERY_BROKER_URL = get_env("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = get_env("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = int(get_env("CELERY_TASK_TIME_LIMIT", 300))


# Security defaults
CSRF_COOKIE_SECURE = get_env("CSRF_COOKIE_SECURE", "False").lower() in ("1", "true", "yes")
SESSION_COOKIE_SECURE = get_env("SESSION_COOKIE_SECURE", "False").lower() in ("1", "true", "yes")
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Authentication URL configuration
LOGIN_URL = "/auth/login/"

if get_env("SECURE_HSTS_SECONDS"):
    SECURE_HSTS_SECONDS = int(get_env("SECURE_HSTS_SECONDS", 31536000))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = get_env("SECURE_HSTS_INCLUDE_SUBDOMAINS", "True").lower() in ("1", "true", "yes")
    SECURE_HSTS_PRELOAD = get_env("SECURE_HSTS_PRELOAD", "True").lower() in ("1", "true", "yes")


# Logging - structured, designed for cloud
LOG_LEVEL = get_env("LOG_LEVEL", "INFO")
LOGGING: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {
            "level": LOG_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "standard",
        }
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
}


# Try to provide a Sentry integration if DSN provided
SENTRY_DSN = get_env("SENTRY_DSN", "")
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            traces_sample_rate=float(get_env("SENTRY_TRACES_SAMPLE_RATE", 0.0)),
        )
    except Exception:
        # don't hard-fail if sentry isn't installed
        pass

# Optional: include simplejwt token blacklist app if available
try:
    __import__("rest_framework_simplejwt.token_blacklist")
except Exception:
    # not installed in this environment; skip
    pass
else:
    INSTALLED_APPS.append("rest_framework_simplejwt.token_blacklist")


# ============================================================================
# Celery Configuration - Async Task Management
# ============================================================================

# Redis connection URL (broker and result backend)
CELERY_BROKER_URL = get_env("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = get_env("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# Celery app settings
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Task configuration
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 600  # 10 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutes

# Result backend config
CELERY_RESULT_EXPIRES = 3600  # Results expire after 1 hour
CELERY_RESULT_EXTENDED = True

# Celery Beat Scheduler (persistent storage for scheduled tasks)
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Email configuration for Celery tasks
EMAIL_BACKEND = "invoicing_app.core.email_backend.DynamicEmailBackend"
EMAIL_HOST = get_env("EMAIL_HOST", "")
EMAIL_PORT = int(get_env("EMAIL_PORT", "465"))
EMAIL_USE_SSL = get_env("EMAIL_USE_SSL", "True").lower() == "true"
EMAIL_USE_TLS = get_env("EMAIL_USE_TLS", "False").lower() == "true"
EMAIL_HOST_USER = get_env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = get_env("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = get_env("DEFAULT_FROM_EMAIL", "")


# ============================================================================
# Stripe Payment Processing (SaaS Commercialization)
# ============================================================================

STRIPE_API_KEY = get_env("STRIPE_API_KEY", "sk_test_YOUR_KEY_HERE")
STRIPE_WEBHOOK_SECRET = get_env("STRIPE_WEBHOOK_SECRET", "whsec_test_YOUR_SECRET_HERE")
STRIPE_PUBLISHABLE_KEY = get_env("STRIPE_PUBLISHABLE_KEY", "pk_test_YOUR_KEY_HERE")

# ============================================================================
# Security Middleware (Production)
# ============================================================================

SECURITY_MIDDLEWARE_ENABLED = get_env("SECURITY_MIDDLEWARE_ENABLED", "True").lower() == "true"

if SECURITY_MIDDLEWARE_ENABLED:
    MIDDLEWARE.insert(0, "invoicing_app.organizations.security.RateLimitMiddleware")
    MIDDLEWARE.insert(1, "invoicing_app.organizations.security.SecurityHeadersMiddleware")
    MIDDLEWARE.insert(2, "invoicing_app.organizations.security.CSPMiddleware")

# ============================================================================
# CORS Configuration (API Access)
# ============================================================================

CORS_ALLOWED_ORIGINS = get_env("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
CORS_ALLOW_CREDENTIALS = True

# ============================================================================
# Multi-Tenancy Configuration
# ============================================================================

MULTI_TENANCY_ENABLED = get_env("MULTI_TENANCY_ENABLED", "True").lower() == "true"
ORGANIZATION_REQUIRED_APPS = [
    "invoicing_app.invoices",
    "invoicing_app.deliveries",
    "invoicing_app.quotations",
    "invoicing_app.payments",
    "invoicing_app.expenses",
    "invoicing_app.clients",
    "invoicing_app.products",
]
