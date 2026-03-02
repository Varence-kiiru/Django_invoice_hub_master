"""App configuration for expenses."""
from django.apps import AppConfig


class ExpensesConfig(AppConfig):
    """Expenses app configuration."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'invoicing_app.expenses'
    verbose_name = 'Expense Tracking'
