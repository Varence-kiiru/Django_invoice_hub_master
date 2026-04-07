"""
Organization role configuration.

Defines roles available for organization members (separate from system-wide UserRole).
This keeps role definitions in one place for easy maintenance.
"""

# Organization member roles and their descriptions
ORGANIZATION_ROLES = [
    {
        "id": "owner",
        "name": "Owner",
        "description": "Full access to organization settings and all features. Can manage team members.",
        "icon": "👑",
        "badge_color": "warning",  # Bootstrap badge color
    },
    {
        "id": "admin",
        "name": "Admin",
        "description": "Full access to features and settings. Can manage most team members.",
        "icon": "🔑",
        "badge_color": "danger",
    },
    {
        "id": "manager",
        "name": "Manager",
        "description": "Can manage invoices, clients, and view reports. Limited settings access.",
        "icon": "📋",
        "badge_color": "info",
    },
    {
        "id": "accountant",
        "name": "Accountant",
        "description": "Can manage payments, expenses, and create financial reports.",
        "icon": "💼",
        "badge_color": "primary",
    },
    {
        "id": "staff",
        "name": "Staff",
        "description": "Can create and manage invoices. Limited reporting access.",
        "icon": "👨‍💼",
        "badge_color": "secondary",
    },
    {
        "id": "viewer",
        "name": "Viewer",
        "description": "Read-only access to most features. Cannot create or edit records.",
        "icon": "👁️",
        "badge_color": "light",
    },
]


def get_all_org_roles():
    """Return all organization roles."""
    return ORGANIZATION_ROLES


def get_org_role(role_id):
    """Get a specific role by ID."""
    for role in ORGANIZATION_ROLES:
        if role["id"] == role_id:
            return role
    return None


def get_valid_role_ids():
    """Return list of valid role IDs."""
    return [role["id"] for role in ORGANIZATION_ROLES]


def get_role_by_name(role_name):
    """Get role info by name (case-insensitive)."""
    role_name_lower = role_name.lower()
    for role in ORGANIZATION_ROLES:
        if role["name"].lower() == role_name_lower:
            return role
    return None
