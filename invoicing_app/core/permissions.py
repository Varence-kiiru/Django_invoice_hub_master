"""Custom permission classes for role-based access control."""

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import permissions
from invoicing_app.user_management.models import CustomUser


class IsAdmin(permissions.BasePermission):
    """
    Permission class for system administration.
    Allows access only to superusers or users with system_admin permission.
    """

    message = "System administration access required."

    def has_permission(self, request, view):
        """Check if user is superuser or has system admin permission."""
        if not request.user or not request.user.is_authenticated:
            return False
        # Superusers always have access
        if request.user.is_superuser:
            return True
        # Check for system admin permission
        return user_has_permission(request.user, "system_admin")


class IsAccountant(permissions.BasePermission):
    """
    Permission class for financial operations.
    Allows access to users with financial management permissions.
    """

    message = "Financial access required."

    def has_permission(self, request, view):
        """Check if user has financial access permissions."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers and system admins have access
        if request.user.is_superuser:
            return True
        if user_has_permission(request.user, "system_admin"):
            return True

        # Check for any financial or accounting permission
        return user_has_any_permission(
            request.user,
            [
                "manage_financials",
                "view_financials",
                "approve_expenses",
                "process_payments",
                "reconcile_payments",
            ],
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission class that allows users to access their own objects or admins to access all.
    """

    message = "You don't have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        """
        Check if the user owns the object or is an admin.
        Assumes obj has a user or created_by field.
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Allow admin access to everything
        try:
            profile = request.user.invoicing_profile
            if profile.role and profile.role.name == "admin":
                return True
        except CustomUser.DoesNotExist:
            return False

        # Check ownership based on available fields
        if hasattr(obj, "user"):
            return obj.user == request.user
        elif hasattr(obj, "created_by"):
            return obj.created_by == request.user
        elif hasattr(obj, "customer"):
            # For invoices, payments, etc. - check if created by current user
            return obj.customer and obj.customer.customer_email == request.user.email

        return False


class IsReadOnlyOrAdmin(permissions.BasePermission):
    """
    Permission class that allows read access to everyone,
    but write access only to admins.
    """

    message = "Only administrators can modify this resource."

    def has_permission(self, request, view):
        """Read operations are allowed, write only for admins."""
        # Allow read methods
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Write methods only for admins
        if not request.user or not request.user.is_authenticated:
            return False

        try:
            profile = request.user.invoicing_profile
            return profile.role and profile.role.name == "admin"
        except CustomUser.DoesNotExist:
            return False


class CanManageUsers(permissions.BasePermission):
    """
    Permission class for user management operations.
    Only admins can create, modify, or delete users.
    Users can view and edit their own profile.
    """

    message = "You don't have permission to manage users."

    def has_permission(self, request, view):
        """Admin can do anything, others only for safe methods on self."""
        if not request.user or not request.user.is_authenticated:
            return False

        try:
            profile = request.user.invoicing_profile
            # Admins can do anything
            if profile.role and profile.role.name == "admin":
                return True
        except CustomUser.DoesNotExist:
            return False

        # Non-admins can only read
        return request.method in permissions.SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        """Users can view/edit their own profile, admins can view/edit all."""
        if not request.user or not request.user.is_authenticated:
            return False

        try:
            profile = request.user.invoicing_profile
            # Admins can access any user
            if profile.role and profile.role.name == "admin":
                return True
        except CustomUser.DoesNotExist:
            return False

        # Users can only access their own profile
        if hasattr(obj, "user"):
            return obj.user == request.user

        return False


class CanViewInvoices(permissions.BasePermission):
    """
    Permission class for viewing invoices.
    Users with view_invoices permission can see invoices based on their role.
    """

    message = "You don't have permission to view invoices."

    def has_permission(self, request, view):
        """Check if user can view any invoices."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if user can access specific invoice based on permissions."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers and system admins can view all
        if request.user.is_superuser or user_has_permission(
            request.user, "system_admin"
        ):
            return True

        # Users with manage invoices permission can view all
        if user_has_permission(request.user, "view_invoices"):
            # Check for restrictions on object level
            if hasattr(obj, "created_by") and obj.created_by == request.user:
                return True
            if hasattr(obj, "assigned_to") and obj.assigned_to == request.user:
                return True
            # If manage permission, allow full access
            if user_has_permission(request.user, "edit_invoices"):
                return True

        # Regular users can only view their own invoices
        if hasattr(obj, "created_by") and obj.created_by == request.user:
            return True
        if hasattr(obj, "assigned_to") and obj.assigned_to == request.user:
            return True

        return False


class CanManagePayments(permissions.BasePermission):
    """
    Permission class for payment management.
    Users with process_payments permission can manage payments.
    Viewing is allowed for invoice creators/owners.
    """

    message = "You don't have permission to manage payments."

    def has_permission(self, request, view):
        """Check if user can access payments endpoint."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Safe methods (GET) allowed for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write methods only for users with process_payments permission
        try:
            return user_has_permission(request.user, "process_payments")
        except:
            return False

    def has_object_permission(self, request, view, obj):
        """Check if user can access specific payment."""
        if not request.user or not request.user.is_authenticated:
            return False

        try:
            # Users with manage payment permissions can access all
            if user_has_permission(request.user, "reconcile_payments"):
                return True
            # Superusers and system admins have access
            if request.user.is_superuser or user_has_permission(
                request.user, "system_admin"
            ):
                return True
        except:
            pass

        # Regular users can only view payments for their invoices
        if hasattr(obj, "invoice") and hasattr(obj.invoice, "created_by"):
            return obj.invoice.created_by == request.user

        return False


class CanViewAuditLogs(permissions.BasePermission):
    """
    Permission class for audit log access.
    Only users with view_audit_logs permission can see system audit logs.
    """

    message = "Audit log access required."

    def has_permission(self, request, view):
        """Check if user can access audit logs."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers and system admins have access
        if request.user.is_superuser:
            return True

        return user_has_permission(request.user, "view_audit_logs")


# ==================== PERMISSION DEFINITIONS ====================
# Define all available permissions in the system
# Format: 'permission_code': 'Human Readable Description'
#
# IMPORTANT: All permissions here are DYNAMICALLY ASSIGNABLE to any role
# Admins can create custom roles and assign any combination of these permissions
# via the Role Management interface. No permissions are locked to specific roles.

EXPENSE_PERMISSIONS = {
    "create_expenses": "Create new expenses",
    "view_all_expenses": "View all expenses",
    "view_own_expenses": "View own expenses only",
    "edit_any_expense": "Edit any expense",
    "edit_own_expenses": "Edit own expenses",
    "edit_own_draft_expenses": "Edit own draft expenses only",
    "delete_any_expense": "Delete any expense",
    "delete_own_expenses": "Delete own expenses",
    "delete_own_draft_expenses": "Delete own draft expenses only",
    "submit_expenses": "Submit expenses for approval",
    "approve_expenses": "Approve/reject submitted expenses",
    "mark_expense_paid": "Mark approved expenses as paid",
}

INVOICE_PERMISSIONS = {
    "create_invoices": "Create invoices",
    "view_invoices": "View invoices",
    "edit_invoices": "Edit invoices",
    "delete_invoices": "Delete invoices",
    "send_invoices": "Send invoices to clients",
    "view_invoice_reports": "View invoice reports",
}

CLIENT_PERMISSIONS = {
    "manage_clients": "Create, edit, delete clients",
    "view_clients": "View client information",
    "view_client_contacts": "View client contact information",
}

PAYMENT_PERMISSIONS = {
    "process_payments": "Process payments",
    "view_payments": "View payment records",
    "manage_payment_methods": "Manage payment methods",
    "reconcile_payments": "Reconcile payment accounts",
}

QUOTATION_PERMISSIONS = {
    "create_quotations": "Create quotations",
    "view_quotations": "View quotations",
    "edit_quotations": "Edit quotations",
    "delete_quotations": "Delete quotations",
    "convert_quotations": "Convert quotations to invoices",
}

USER_PERMISSIONS = {
    "manage_users": "Create, edit, deactivate users",
    "view_users": "View user information",
    "edit_own_profile": "Edit own profile",
    "view_audit_logs": "View audit logs",
}

SYSTEM_PERMISSIONS = {
    "configure_settings": "Configure system settings",
    "manage_roles": "Manage user roles and permissions",
    "manage_backups": "Create and restore backups",
    "system_admin": "Full system administration access",
}

REPORT_PERMISSIONS = {
    "view_reports": "View reports",
    "export_reports": "Export report data",
    "create_custom_reports": "Create custom reports",
}

FINANCIAL_PERMISSIONS = {
    "view_financials": "View financial data and reports",
    "manage_financials": "Manage financial records and settings",
    "view_financial_reports": "View detailed financial reports",
    "export_financial_data": "Export financial data",
}

# Combine all permissions
ALL_PERMISSIONS = {
    **EXPENSE_PERMISSIONS,
    **INVOICE_PERMISSIONS,
    **CLIENT_PERMISSIONS,
    **PAYMENT_PERMISSIONS,
    **QUOTATION_PERMISSIONS,
    **USER_PERMISSIONS,
    **SYSTEM_PERMISSIONS,
    **REPORT_PERMISSIONS,
    **FINANCIAL_PERMISSIONS,
}

# ==================== PERMISSION CHECKING UTILITIES ====================


def user_has_permission(user, permission_code):
    """
    Check if a user has a specific permission.

    Args:
        user: Django User instance
        permission_code: Permission code string (e.g., 'approve_expenses')

    Returns:
        bool: True if user has permission, False otherwise
    """
    # Superusers have all permissions
    if user.is_superuser:
        return True

    try:
        # Get the user's role through invoicing_profile
        profile = user.invoicing_profile
        if not profile.role or not profile.role.permissions:
            return False

        perms = profile.role.permissions

        # Handle both dict and list formats
        if isinstance(perms, dict):
            # Dict format: {'view_invoices': True, 'view_payments': False}
            return perms.get(permission_code, False)
        elif isinstance(perms, list):
            # List format: ['view_invoices', 'view_payments']
            return permission_code in perms
        else:
            return False

    except Exception:
        return False


def user_has_any_permission(user, permission_codes):
    """
    Check if a user has any of the specified permissions.

    Args:
        user: Django User instance
        permission_codes: List of permission code strings

    Returns:
        bool: True if user has any permission, False otherwise
    """
    return any(user_has_permission(user, perm) for perm in permission_codes)


def user_has_all_permissions(user, permission_codes):
    """
    Check if a user has all of the specified permissions.

    Args:
        user: Django User instance
        permission_codes: List of permission code strings

    Returns:
        bool: True if user has all permissions, False otherwise
    """
    return all(user_has_permission(user, perm) for perm in permission_codes)


def get_user_permissions(user):
    """
    Get all permissions for a user.

    Args:
        user: Django User instance

    Returns:
        list: List of permission codes the user has
    """
    if user.is_superuser:
        return list(ALL_PERMISSIONS.keys())

    try:
        profile = user.invoicing_profile
        if profile.role:
            return profile.role.permissions
        return []
    except (AttributeError, ObjectDoesNotExist):
        return []


# ==================== PERMISSION GROUP HELPERS ====================


def get_permission_group(group_name):
    """Get permission group by name"""
    groups = {
        "expenses": EXPENSE_PERMISSIONS,
        "invoices": INVOICE_PERMISSIONS,
        "clients": CLIENT_PERMISSIONS,
        "payments": PAYMENT_PERMISSIONS,
        "quotations": QUOTATION_PERMISSIONS,
        "users": USER_PERMISSIONS,
        "system": SYSTEM_PERMISSIONS,
        "reports": REPORT_PERMISSIONS,
        "financials": FINANCIAL_PERMISSIONS,
    }
    return groups.get(group_name, {})


def get_all_permission_groups():
    """Get all permission groups organized by category"""
    return {
        "expenses": EXPENSE_PERMISSIONS,
        "invoices": INVOICE_PERMISSIONS,
        "clients": CLIENT_PERMISSIONS,
        "payments": PAYMENT_PERMISSIONS,
        "quotations": QUOTATION_PERMISSIONS,
        "users": USER_PERMISSIONS,
        "system": SYSTEM_PERMISSIONS,
        "reports": REPORT_PERMISSIONS,
        "financials": FINANCIAL_PERMISSIONS,
    }


def get_all_permissions_inventory():
    """
    Get complete inventory of all permissions organized by category with descriptions.
    Useful for documentation, permission management UI, and audit purposes.

    Returns:
        dict: Organized permission inventory
            {
                'category_name': {
                    'display_name': 'Category Display Name',
                    'permissions': {
                        'permission_code': 'Description',
                        ...
                    }
                },
                ...
            }
    """
    categories = {
        "expenses": {
            "display_name": "💸 Expenses",
            "description": "Manage expense tracking and reimbursement",
            "permissions": EXPENSE_PERMISSIONS,
        },
        "invoices": {
            "display_name": "📄 Invoices",
            "description": "Create, edit, and manage invoices",
            "permissions": INVOICE_PERMISSIONS,
        },
        "clients": {
            "display_name": "👥 Clients",
            "description": "Manage client information and relationships",
            "permissions": CLIENT_PERMISSIONS,
        },
        "payments": {
            "display_name": "💳 Payments",
            "description": "Process and reconcile payments",
            "permissions": PAYMENT_PERMISSIONS,
        },
        "quotations": {
            "display_name": "📋 Quotations",
            "description": "Create and manage quotations/estimates",
            "permissions": QUOTATION_PERMISSIONS,
        },
        "users": {
            "display_name": "👤 Users",
            "description": "Manage user accounts and profiles",
            "permissions": USER_PERMISSIONS,
        },
        "system": {
            "display_name": "⚙️ System",
            "description": "System administration and configuration",
            "permissions": SYSTEM_PERMISSIONS,
        },
        "reports": {
            "display_name": "📊 Reports",
            "description": "View and export business reports",
            "permissions": REPORT_PERMISSIONS,
        },
        "financials": {
            "display_name": "💰 Financials",
            "description": "Access financial data and reports",
            "permissions": FINANCIAL_PERMISSIONS,
        },
    }
    return categories


def get_permission_stats():
    """
    Get statistics about available permissions.

    Returns:
        dict: Stats including total, by category, and assignability info
    """
    all_perms = ALL_PERMISSIONS
    inventory = get_all_permissions_inventory()

    stats = {
        "total_permissions": len(all_perms),
        "total_categories": len(inventory),
        "by_category": {},
        "all_dynamically_assignable": True,
    }

    for category_key, category_data in inventory.items():
        perms = category_data["permissions"]
        stats["by_category"][category_key] = {
            "display_name": category_data["display_name"],
            "count": len(perms),
            "dynamically_assignable": True,  # All permissions are assignable
        }

    return stats


def can_view_financials(user):
    """
    Check if user can view financial data.
    Based on dynamic role permissions, not hardcoded role names.
    """
    if not user or not user.is_authenticated:
        return False
    return user_has_permission(user, "view_financials")


def can_manage_financials(user):
    """
    Check if user can manage financial data.
    Based on dynamic role permissions, not hardcoded role names.
    """
    if not user or not user.is_authenticated:
        return False
    return user_has_permission(user, "manage_financials")


# ==================== DECORATORS ====================


def permission_required(*permission_codes):
    """
    Decorator to check if user has required permissions before allowing access to a view.
    Supports checking for any of multiple permissions (OR logic).

    Usage:
        @login_required
        @permission_required("manage_users", "system_admin")  # User needs ANY of these
        def my_view(request):
            ...
    """
    from django.contrib.auth.decorators import login_required
    from functools import wraps
    from django.shortcuts import redirect
    from django.contrib import messages

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("organizations:login")

            # Check if user has ANY of the required permissions
            has_permission = user_has_any_permission(request.user, permission_codes)

            if not has_permission:
                messages.error(
                    request, "You do not have permission to access this page."
                )
                return redirect("core:dashboard")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
