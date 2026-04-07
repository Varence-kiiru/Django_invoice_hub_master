"""
Authentication and authorization models.
"""

from django.db import models
from invoicing_app.core.models import BaseModel


class UserRole(models.Model):
    """
    Custom role definitions with permissions (extensible).
    Roles can be created dynamically and automatically integrated into the system.
    """

    # Role hierarchy levels for permission checking
    ROLE_HIERARCHY = {
        "admin": 4,  # Super admin - full access
        "manager": 3,  # Manager - elevated access
        "staff": 2,  # Staff - standard operations
        "user": 1,  # User - basic access
    }

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Role name, e.g., 'admin', 'accountant'",
    )
    description = models.TextField(
        blank=True, null=True, help_text="Human-readable role description"
    )
    permissions = models.JSONField(
        default=list, help_text="List of permission codes this role has"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="When this role was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True, help_text="When this role was last updated"
    )
    is_active = models.BooleanField(
        default=True, db_index=True, help_text="Whether this role is active"
    )

    class Meta:
        db_table = "user_management_userrole"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.name} ({len(self.permissions)} permissions)"

    def get_hierarchy_level(self):
        """Get role hierarchy level for permission checking"""
        return self.ROLE_HIERARCHY.get(self.name, 0)

    def is_at_least(self, role_name):
        """Check if this role has same or higher level than the specified role"""
        return self.get_hierarchy_level() >= self.ROLE_HIERARCHY.get(role_name, 0)

    def get_icon(self):
        """Get icon for this role"""
        icons = {
            "superadmin": "⭐",
            "admin": "👑",
            "manager": "📋",
            "staff": "👨‍💼",
            "user": "👤",
            "accountant": "💼",
            "viewer": "👁️",
        }
        return icons.get(self.name, "🔑")

    def get_display_name(self):
        """Get human-readable display name for this role"""
        return self.name.replace("_", " ").title()

    def can_manage_role(self, other_role_name):
        """Check if this role can manage another role"""
        # Hierarchy: admin > manager > staff > user
        return self.get_hierarchy_level() > self.ROLE_HIERARCHY.get(other_role_name, 0)


class CustomUser(BaseModel):
    """
    Custom user extension model that complements Django's built-in User.
    Stores invoicing-specific user data while allowing Django admin/auth to work.
    """

    # Link to Django's built-in User model
    user = models.OneToOneField(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="invoicing_profile",
        help_text="Link to Django's built-in User",
    )
    phone = models.CharField(
        max_length=20, blank=True, null=True, help_text="User's phone number"
    )
    role = models.ForeignKey(
        UserRole,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="users",
        db_index=True,
        help_text="User's role (dynamically defined)",
    )
    created_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_users",
        help_text="User who created this account (for audit)",
    )

    class Meta:
        db_table = "user_management_customuser"
        ordering = ["user__email"]
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        role_display = self.role.name if self.role else "No Role"
        return f"{self.user.email} ({role_display})"

    def get_full_name(self):
        """Return full name of user."""
        return self.user.get_full_name() or self.user.email

    def get_role_name(self):
        """Get role name safely"""
        return self.role.name if self.role else None

    def has_role(self, role_name):
        """Check if user has specific role"""
        return self.role and self.role.name == role_name

    def has_role_at_least(self, role_name):
        """Check if user has same or higher role level"""
        if not self.role:
            return False
        return self.role.is_at_least(role_name)
