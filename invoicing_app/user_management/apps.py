from django.apps import AppConfig
from django.db.models.signals import post_migrate


class UserManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "invoicing_app.user_management"
    verbose_name = "User Management"

    def ready(self):
        """Initialize app: create default roles after migrations complete."""
        # Import here to avoid circular imports
        from django.dispatch import receiver

        @receiver(post_migrate)
        def create_default_roles(sender, **kwargs):
            """
            Create default system roles if they don't exist.
            This runs automatically after migrations complete.
            Only executes when user_management app migrations are done.
            """
            # Only run when THIS app (user_management) is being migrated
            if sender.name != "invoicing_app.user_management":
                return

            try:
                from .models import UserRole

                # Define all permissions that exist in the system
                all_permissions = [
                    "create_invoices",
                    "view_invoices",
                    "edit_invoices",
                    "delete_invoices",
                    "send_invoices",
                    "view_invoice_reports",
                    "create_quotations",
                    "view_quotations",
                    "edit_quotations",
                    "delete_quotations",
                    "convert_quotations",
                    "process_payments",
                    "view_payments",
                    "manage_payment_methods",
                    "reconcile_payments",
                    "view_all_expenses",
                    "create_expenses",
                    "edit_any_expense",
                    "delete_any_expense",
                    "submit_expenses",
                    "approve_expenses",
                    "mark_expense_paid",
                    "manage_clients",
                    "view_clients",
                    "view_client_contacts",
                    "view_deliveries",
                    "create_deliveries",
                    "edit_deliveries",
                    "delete_deliveries",
                    "view_financials",
                    "manage_financials",
                    "view_financial_reports",
                    "export_financial_data",
                    "view_reports",
                    "export_reports",
                    "create_custom_reports",
                    "manage_users",
                    "view_users",
                    "edit_own_profile",
                    "view_audit_logs",
                    "manage_roles",
                    "configure_settings",
                    "manage_backups",
                    "system_admin",
                    "manage_tax_rates",
                    "manage_products",
                ]

                # Define all default roles
                default_roles = [
                    {
                        "name": "superadmin",
                        "description": "Super Administrator with complete system access and control",
                        "permissions": all_permissions,  # ALL permissions
                    },
                    {
                        "name": "admin",
                        "description": "Administrator with access to most functions except system backups",
                        "permissions": [
                            p
                            for p in all_permissions
                            if p not in ["manage_backups", "system_admin"]
                        ],
                    },
                    {
                        "name": "manager",
                        "description": "Manager with access to invoicing, clients, and reports",
                        "permissions": [
                            "create_invoices",
                            "view_invoices",
                            "edit_invoices",
                            "delete_invoices",
                            "send_invoices",
                            "view_invoice_reports",
                            "create_quotations",
                            "view_quotations",
                            "edit_quotations",
                            "delete_quotations",
                            "convert_quotations",
                            "process_payments",
                            "view_payments",
                            "view_all_expenses",
                            "create_expenses",
                            "edit_any_expense",
                            "delete_any_expense",
                            "submit_expenses",
                            "manage_clients",
                            "view_clients",
                            "view_client_contacts",
                            "view_deliveries",
                            "view_reports",
                            "export_reports",
                            "view_users",
                            "edit_own_profile",
                            "view_audit_logs",
                            "manage_products",
                        ],
                    },
                    {
                        "name": "staff",
                        "description": "Staff member with access to invoices and clients",
                        "permissions": [
                            "view_invoices",
                            "edit_invoices",
                            "create_invoices",
                            "view_quotations",
                            "create_quotations",
                            "view_payments",
                            "view_all_expenses",
                            "create_expenses",
                            "edit_own_expenses",
                            "submit_expenses",
                            "view_clients",
                            "manage_clients",
                            "view_deliveries",
                            "view_users",
                            "edit_own_profile",
                        ],
                    },
                    {
                        "name": "user",
                        "description": "Regular user with limited access",
                        "permissions": [
                            "view_invoices",
                            "view_quotations",
                            "view_payments",
                            "view_own_expenses",
                            "view_clients",
                            "view_users",
                            "edit_own_profile",
                        ],
                    },
                    {
                        "name": "accountant",
                        "description": "Accountant with access to financials and payments",
                        "permissions": [
                            "view_invoices",
                            "create_invoices",
                            "edit_invoices",
                            "process_payments",
                            "view_payments",
                            "manage_payment_methods",
                            "reconcile_payments",
                            "view_all_expenses",
                            "create_expenses",
                            "edit_any_expense",
                            "mark_expense_paid",
                            "approve_expenses",
                            "view_financials",
                            "manage_financials",
                            "view_financial_reports",
                            "export_financial_data",
                            "view_reports",
                            "export_reports",
                            "view_users",
                            "edit_own_profile",
                            "view_audit_logs",
                            "manage_tax_rates",
                        ],
                    },
                    {
                        "name": "viewer",
                        "description": "Read-only viewer with access to reports and dashboards",
                        "permissions": [
                            "view_invoices",
                            "view_quotations",
                            "view_payments",
                            "view_all_expenses",
                            "view_clients",
                            "view_deliveries",
                            "view_financials",
                            "view_financial_reports",
                            "view_reports",
                            "view_users",
                        ],
                    },
                ]

                # Create roles if they don't already exist (idempotent)
                for role_data in default_roles:
                    UserRole.objects.get_or_create(
                        name=role_data["name"],
                        defaults={
                            "description": role_data["description"],
                            "is_active": True,
                            "permissions": role_data["permissions"],
                        },
                    )
            except Exception:
                # Silently fail if tables don't exist yet or import fails
                # The roles will be created on next migrate run
                pass
