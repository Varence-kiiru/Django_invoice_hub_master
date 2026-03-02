"""Custom permission classes for role-based access control."""
from rest_framework import permissions
from invoicing_app.user_management.models import CustomUser


class IsAdmin(permissions.BasePermission):
    """
    Permission class that allows access only to admin users.
    """
    message = "Only administrators have access to this resource."

    def has_permission(self, request, view):
        """Check if user is authenticated and has admin role."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            profile = request.user.invoicing_profile
            return profile.role == 'admin'
        except CustomUser.DoesNotExist:
            return False


class IsAccountant(permissions.BasePermission):
    """
    Permission class that allows access for admin and accountant users.
    """
    message = "Only administrators and accountants have access to this resource."

    def has_permission(self, request, view):
        """Check if user is authenticated and has accountant or admin role."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            profile = request.user.invoicing_profile
            return profile.role in ['admin', 'accountant']
        except CustomUser.DoesNotExist:
            return False


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
            if profile.role == 'admin':
                return True
        except CustomUser.DoesNotExist:
            return False
        
        # Check ownership based on available fields
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'customer'):
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
            return profile.role == 'admin'
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
            if profile.role == 'admin':
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
            if profile.role == 'admin':
                return True
        except CustomUser.DoesNotExist:
            return False
        
        # Users can only access their own profile
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class CanViewInvoices(permissions.BasePermission):
    """
    Permission class for viewing invoices.
    Admins and accountants can view all invoices.
    Regular users can view their own invoices.
    """
    message = "You don't have permission to view this invoice."

    def has_permission(self, request, view):
        """All authenticated users can view invoices (filtered by role)."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if user can access specific invoice."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            profile = request.user.invoicing_profile
            # Admins and accountants can view all invoices
            if profile.role in ['admin', 'accountant']:
                return True
            
            # Regular users can only view invoices they created or are assigned to
            if hasattr(obj, 'created_by') and obj.created_by == request.user:
                return True
            if hasattr(obj, 'assigned_to') and obj.assigned_to == request.user:
                return True
        except CustomUser.DoesNotExist:
            pass
        
        return False


class CanManagePayments(permissions.BasePermission):
    """
    Permission class for payment management.
    Only admins and accountants can record/modify payments.
    All users can view payments for their invoices.
    """
    message = "You don't have permission to manage payments."

    def has_permission(self, request, view):
        """Check if user can access payments endpoint."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Safe methods (GET) allowed for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write methods only for accountants and admins
        try:
            profile = request.user.invoicing_profile
            return profile.role in ['admin', 'accountant']
        except CustomUser.DoesNotExist:
            return False

    def has_object_permission(self, request, view, obj):
        """Check if user can access specific payment."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            profile = request.user.invoicing_profile
            # Admins and accountants can access all payments
            if profile.role in ['admin', 'accountant']:
                return True
        except CustomUser.DoesNotExist:
            pass
        
        # Regular users can only view payments for their invoices
        if hasattr(obj, 'invoice') and hasattr(obj.invoice, 'created_by'):
            return obj.invoice.created_by == request.user
        
        return False


class CanViewAuditLogs(permissions.BasePermission):
    """
    Permission class for audit log access.
    Only admins and accountants can view audit logs.
    """
    message = "Only administrators and accountants can view audit logs."

    def has_permission(self, request, view):
        """Check if user can access audit logs."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            profile = request.user.invoicing_profile
            return profile.role in ['admin', 'accountant']
        except CustomUser.DoesNotExist:
            return False


# ==================== PERMISSION DEFINITIONS ====================
# Define all available permissions in the system
# Format: 'permission_code': 'Human Readable Description'

EXPENSE_PERMISSIONS = {
    'create_expenses': 'Create new expenses',
    'view_all_expenses': 'View all expenses',
    'view_own_expenses': 'View own expenses only',
    'edit_any_expense': 'Edit any expense',
    'edit_own_expenses': 'Edit own expenses',
    'edit_own_draft_expenses': 'Edit own draft expenses only',
    'delete_any_expense': 'Delete any expense',
    'delete_own_expenses': 'Delete own expenses',
    'delete_own_draft_expenses': 'Delete own draft expenses only',
    'submit_expenses': 'Submit expenses for approval',
    'approve_expenses': 'Approve/reject submitted expenses',
    'mark_expense_paid': 'Mark approved expenses as paid',
}

INVOICE_PERMISSIONS = {
    'create_invoices': 'Create invoices',
    'view_invoices': 'View invoices',
    'edit_invoices': 'Edit invoices',
    'delete_invoices': 'Delete invoices',
    'send_invoices': 'Send invoices to clients',
    'view_invoice_reports': 'View invoice reports',
}

CLIENT_PERMISSIONS = {
    'manage_clients': 'Create, edit, delete clients',
    'view_clients': 'View client information',
    'view_client_contacts': 'View client contact information',
}

PAYMENT_PERMISSIONS = {
    'process_payments': 'Process payments',
    'view_payments': 'View payment records',
    'manage_payment_methods': 'Manage payment methods',
    'reconcile_payments': 'Reconcile payment accounts',
}

QUOTATION_PERMISSIONS = {
    'create_quotations': 'Create quotations',
    'view_quotations': 'View quotations',
    'edit_quotations': 'Edit quotations',
    'delete_quotations': 'Delete quotations',
    'convert_quotations': 'Convert quotations to invoices',
}

USER_PERMISSIONS = {
    'manage_users': 'Create, edit, deactivate users',
    'view_users': 'View user information',
    'edit_own_profile': 'Edit own profile',
    'view_audit_logs': 'View audit logs',
}

SYSTEM_PERMISSIONS = {
    'configure_settings': 'Configure system settings',
    'manage_roles': 'Manage user roles and permissions',
    'manage_backups': 'Create and restore backups',
    'system_admin': 'Full system administration access',
}

REPORT_PERMISSIONS = {
    'view_reports': 'View reports',
    'export_reports': 'Export report data',
    'create_custom_reports': 'Create custom reports',
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
            
    except Exception as e:
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
    except:
        return []


# ==================== PERMISSION GROUP HELPERS ====================

def get_permission_group(group_name):
    """Get permission group by name"""
    groups = {
        'expenses': EXPENSE_PERMISSIONS,
        'invoices': INVOICE_PERMISSIONS,
        'clients': CLIENT_PERMISSIONS,
        'payments': PAYMENT_PERMISSIONS,
        'quotations': QUOTATION_PERMISSIONS,
        'users': USER_PERMISSIONS,
        'system': SYSTEM_PERMISSIONS,
        'reports': REPORT_PERMISSIONS,
    }
    return groups.get(group_name, {})


def get_all_permission_groups():
    """Get all permission groups organized by category"""
    return {
        'expenses': EXPENSE_PERMISSIONS,
        'invoices': INVOICE_PERMISSIONS,
        'clients': CLIENT_PERMISSIONS,
        'payments': PAYMENT_PERMISSIONS,
        'quotations': QUOTATION_PERMISSIONS,
        'users': USER_PERMISSIONS,
        'system': SYSTEM_PERMISSIONS,
        'reports': REPORT_PERMISSIONS,
    }
