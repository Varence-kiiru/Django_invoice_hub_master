"""
Breadcrumb Navigation Configuration and Utilities

This module provides utilities for building breadcrumb navigation trails
consistently across the application.

Usage in views:
    breadcrumbs = BreadcrumbBuilder()
    breadcrumbs.add('Dashboard', 'core:dashboard')
    breadcrumbs.add('Users', 'user_management:list')
    breadcrumbs.add(f'User: {user.name}')  # Current page (no URL)
    context['breadcrumbs'] = breadcrumbs.build()
"""

from django.urls import reverse
from typing import List, Dict, Optional


class BreadcrumbBuilder:
    """Builder for constructing breadcrumb navigation trails."""

    def __init__(self):
        """Initialize the breadcrumb builder."""
        self.items: List[Dict[str, str]] = []

    def add(
        self,
        label: str,
        url_name: Optional[str] = None,
        url_kwargs: Optional[Dict] = None,
        url: Optional[str] = None,
    ) -> "BreadcrumbBuilder":
        """
        Add a breadcrumb item.

        Args:
            label: Display text for the breadcrumb
            url_name: Django URL name (e.g., 'core:dashboard'). Will use reverse()
            url_kwargs: Kwargs to pass to reverse() if url_name is provided
            url: Direct URL path (alternative to url_name)

        Returns:
            self for method chaining
        """
        item = {"label": label}

        if url_name:
            try:
                item["url"] = reverse(url_name, kwargs=url_kwargs or {})
            except Exception:
                # If URL name doesn't exist, treat as current page
                item["url"] = ""
        elif url:
            item["url"] = url
        else:
            # No URL = current page indicator
            item["url"] = ""

        self.items.append(item)
        return self

    def add_home(self) -> "BreadcrumbBuilder":
        """Add 'Dashboard' as first breadcrumb item."""
        return self.add("Dashboard", "core:dashboard")

    def add_section(
        self, section_name: str, section_url_name: str
    ) -> "BreadcrumbBuilder":
        """
        Add a section breadcrumb (e.g., 'Users', 'Invoices').

        Args:
            section_name: Display name of the section
            section_url_name: Django URL name for the section list/dashboard

        Returns:
            self for method chaining
        """
        return self.add(section_name, section_url_name)

    def add_current(self, label: str) -> "BreadcrumbBuilder":
        """
        Add a breadcrumb for the current page (without URL).

        Args:
            label: Display text for the current page

        Returns:
            self for method chaining
        """
        self.items.append({"label": label, "url": ""})
        return self

    def build(self) -> List[Dict[str, str]]:
        """
        Build and return the breadcrumb list.

        Returns:
            List of breadcrumb items with 'label' and optional 'url'
        """
        return self.items

    def clear(self) -> "BreadcrumbBuilder":
        """Clear all breadcrumb items."""
        self.items = []
        return self

    def __len__(self) -> int:
        """Return the number of breadcrumb items."""
        return len(self.items)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"BreadcrumbBuilder({len(self.items)} items)"


# Predefined breadcrumb patterns for common page hierarchies
BREADCRUMB_PATTERNS = {
    "dashboard": [{"label": "Dashboard", "url": "core:dashboard"}],
    "users": [
        {"label": "Dashboard", "url": "core:dashboard"},
        {"label": "Users", "url": "user_management:list"},
    ],
    "invoices": [
        {"label": "Dashboard", "url": "core:dashboard"},
        {"label": "Invoices", "url": "invoices:list"},
    ],
    "quotations": [
        {"label": "Dashboard", "url": "core:dashboard"},
        {"label": "Quotations", "url": "quotations:list"},
    ],
    "clients": [
        {"label": "Dashboard", "url": "core:dashboard"},
        {"label": "Clients", "url": "clients:list"},
    ],
    "products": [
        {"label": "Dashboard", "url": "core:dashboard"},
        {"label": "Products", "url": "products:list"},
    ],
    "payments": [
        {"label": "Dashboard", "url": "core:dashboard"},
        {"label": "Payments", "url": "payments:list"},
    ],
    "expenses": [
        {"label": "Dashboard", "url": "core:dashboard"},
        {"label": "Expenses", "url": "expenses:list"},
    ],
    "reports": [
        {"label": "Dashboard", "url": "core:dashboard"},
        {"label": "Reports", "url": "core:reports"},
    ],
    "settings": [
        {"label": "Dashboard", "url": "core:dashboard"},
        {"label": "Settings", "url": "settings:index"},
    ],
}


def get_pattern(pattern_name: str) -> List[Dict[str, str]]:
    """
    Get a predefined breadcrumb pattern by name.

    Args:
        pattern_name: Name of the pattern (e.g., 'users', 'invoices')

    Returns:
        List of breadcrumb items or empty list if pattern not found
    """
    return BREADCRUMB_PATTERNS.get(pattern_name, [])


def build_breadcrumbs_from_pattern(
    pattern_name: str, current_page: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Build breadcrumbs from a predefined pattern and optionally add current page.

    Args:
        pattern_name: Name of the pattern ('users', 'invoices', etc.)
        current_page: Optional label for the current page to append

    Returns:
        List of breadcrumb items
    """
    builder = BreadcrumbBuilder()

    # Add pattern items
    pattern = get_pattern(pattern_name)
    for item in pattern:
        builder.items.append(item.copy())

    # Add current page if provided
    if current_page:
        builder.add_current(current_page)

    return builder.build()


def inject_breadcrumbs_context(
    view_func,
) -> callable:
    """
    Decorator to inject empty breadcrumbs context (for views that need it).

    Usage:
        @inject_breadcrumbs_context
        def my_view(request):
            # View code here
            return render(request, 'template.html', context)
    """

    def wrapper(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        if isinstance(response, dict):
            response.setdefault("breadcrumbs", [])
        return response

    return wrapper
