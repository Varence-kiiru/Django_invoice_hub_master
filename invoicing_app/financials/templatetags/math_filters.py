"""Custom template tags and filters for financials app."""

from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def div(value, arg):
    """Divide value by arg.

    Usage: {{ 100|div:5 }} outputs 20
    """
    try:
        return Decimal(value) / Decimal(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def mul(value, arg):
    """Multiply value by arg.

    Usage: {{ 25|mul:4 }} outputs 100
    """
    try:
        return Decimal(value) * Decimal(arg)
    except (ValueError, TypeError):
        return 0
