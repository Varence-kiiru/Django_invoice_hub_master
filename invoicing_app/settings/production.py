"""Production settings — secure defaults and environment-driven config.

Adjust environment variables to your cloud provider (Azure/AWS/GCP).
"""

from .base import *  # noqa: F401,F403

DEBUG = False

ALLOWED_HOSTS = get_env("DJANGO_ALLOWED_HOSTS", "").split(",") if get_env("DJANGO_ALLOWED_HOSTS", "") else []

# Strict security defaults
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = get_env("SECURE_SSL_REDIRECT", "True").lower() in ("1", "true", "yes")

# Database: require env variables in production
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": _get_env("MYSQL_DATABASE"),
        "USER": _get_env("MYSQL_USER"),
        "PASSWORD": _get_env("MYSQL_PASSWORD"),
        "HOST": _get_env("MYSQL_HOST"),
        "PORT": _get_env("MYSQL_PORT", "3306"),
        "OPTIONS": {"init_command": "SET sql_mode='STRICT_TRANS_TABLES'"},
    }
}

# Static files should be served by CDN / web server in production; collectstatic into STATIC_ROOT
STATICFILES_STORAGE = _get_env("STATICFILES_STORAGE", "django.contrib.staticfiles.storage.ManifestStaticFilesStorage")

# Cache: prefer Redis or Memcached for production
if _get_env("REDIS_URL"):
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": _get_env("REDIS_URL"),
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        }
    }

# Logging: send WARNING+ to error tracking integrations and INFO to stdout
LOGGING["handlers"]["console"]["level"] = _get_env("LOG_LEVEL", "INFO")
LOGGING["root"]["level"] = _get_env("LOG_LEVEL", "INFO")
