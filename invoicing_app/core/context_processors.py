"""
Context processors for invoicing app.
These functions are called on every request and add variables to the template context.
"""

from .models import CompanySettings
from .permissions import get_user_permissions, user_has_permission


def company_settings(request):
    """
    Add company settings to every template context.

    Provides settings under both 'company_settings' and 'settings' keys for compatibility.

    Usage in templates:
        {{ settings.company_name }}
        {% if settings.enable_export %}...{% endif %}

        {{ company_settings.enable_payments }}

    Returns:
        dict: Dictionary with 'company_settings' and 'settings' keys
    """
    try:
        settings_obj = CompanySettings.get_settings()
        return {
            "company_settings": settings_obj,
            "settings": settings_obj,  # Alias for convenience
        }
    except Exception:
        # If there's any error, return empty dict to avoid breaking templates
        return {
            "company_settings": None,
            "settings": None,
        }


def user_permissions(request):
    """
    Add user permissions and permission checking utilities to every template context.

    Makes permission checks available in all templates without modifying individual views.

    Provides:
    - user_permissions: List of all permissions the user has
    - Granular boolean flags for each permission category (can_view_invoices, can_manage_users, etc.)
    - Helper function: user_has_permission(permission_code) for custom checks

    Usage in templates:
        {% if can_view_invoices %}...{% endif %}
        {% if can_manage_users or can_manage_roles %}...{% endif %}
        {% if user_has_permission 'view_reports' %}...{% endif %}

    Returns:
        dict: Dictionary with permission flags and utilities
    """
    context = {
        "user_permissions": [],
        "user_has_permission": lambda perm: False,
        "is_admin": False,
    }

    # Only add permissions if user is authenticated
    if not request.user or not request.user.is_authenticated:
        return context

    try:
        # Get user's actual permissions
        user = request.user
        is_admin = user.is_superuser
        user_permissions_list = get_user_permissions(user) if not is_admin else []

        # Create permission checking function for use in templates
        def check_permission(perm_code):
            return user_has_permission(user, perm_code) or is_admin

        # Add main permission data
        context["user_permissions"] = user_permissions_list
        context["user_has_permission"] = check_permission
        context["is_admin"] = is_admin

        # Add granular boolean flags for each main section
        # This allows {% if can_view_invoices %} without calling a function
        context["can_view_invoices"] = check_permission("view_invoices")
        context["can_view_quotations"] = check_permission("view_quotations")
        context["can_view_payments"] = check_permission("view_payments")
        context["can_view_clients"] = check_permission("view_clients")
        context["can_view_expenses"] = check_permission(
            "view_all_expenses"
        ) or check_permission("view_own_expenses")
        context["can_view_reports"] = check_permission("view_reports")
        context["can_view_audit_logs"] = check_permission("view_audit_logs")
        context["can_view_financials"] = check_permission("view_financials")
        context["can_view_deliveries"] = check_permission("view_deliveries")
        context["can_manage_users"] = check_permission("manage_users")
        context["can_manage_roles"] = check_permission("manage_roles")
        context["can_manage_settings"] = check_permission("configure_settings")
        context["can_manage_products"] = check_permission("manage_products")
        context["can_manage_taxes"] = check_permission("manage_tax_rates")

        return context

    except Exception:
        # If there's any error, return safe defaults
        return context


def app_version(request):
    """
    Add application version information to every template context.

    Provides version information for display in footer, about page, etc.

    Usage in templates:
        Version {{ app_version }}
        {{ version_name }} - {{ api_version }}

    Returns:
        dict: Dictionary with version information
    """
    try:
        from invoicing_app import __version__, __version_name__, __api_version__

        return {
            "app_version": __version__,
            "version_name": __version_name__,
            "api_version": __api_version__,
        }
    except (ImportError, AttributeError):
        # Fallback if version info is not available
        return {
            "app_version": "4.5.0",
            "version_name": "Complete Financial Intelligence",
            "api_version": "v2.1",
        }
