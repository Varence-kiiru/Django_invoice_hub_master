"""
Custom template filters for timezone-aware datetime formatting.
"""

from django import template
from django.utils import timezone, dateformat
import pytz

register = template.Library()


@register.filter
def company_datetime(value, format_string="M d, Y H:i"):
    """
    Format a datetime to the company's configured timezone using Django format strings.

    Usage: {{ invoice.created_at|company_datetime:"M d, Y \\a\\t H:i" }}
    """
    if not value:
        return ""

    try:
        # Import here to avoid AppRegistryNotReady error
        from invoicing_app.core.models import CompanySettings

        # Get company settings
        settings = CompanySettings.get_settings()
        if not settings or not settings.timezone:
            # Fallback to standard Django date formatting
            return dateformat.format(value, format_string)

        # Convert to company timezone
        tz = pytz.timezone(settings.timezone)
        if timezone.is_naive(value):
            # If datetime is naive, assume it's UTC
            value = timezone.make_aware(value, timezone.utc)

        localized_time = value.astimezone(tz)

        # Use Django's dateformat to properly format with Django format strings
        return dateformat.format(localized_time, format_string)
    except Exception:
        # Fallback to standard formatting
        return dateformat.format(value, format_string)


@register.filter
def company_datetime_short(value):
    """
    Format a datetime to the company's configured timezone with short format.

    Usage: {{ invoice.created_at|company_datetime_short }}
    """
    return company_datetime(value, "M d, Y")


@register.filter
def company_datetime_full(value):
    """
    Format a datetime to the company's configured timezone with full format including time.

    Usage: {{ invoice.created_at|company_datetime_full }}
    """
    return company_datetime(value, "M d, Y H:i")


@register.filter
def format_permission_name(value):
    """
    Convert permission code to human-readable format.
    Example: 'create_invoices' becomes 'Create Invoices'

    Usage: {{ perm_code|format_permission_name }}
    """
    if not value:
        return ""
    # Replace underscores with spaces and title case
    return value.replace("_", " ").title()
