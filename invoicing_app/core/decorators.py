"""
Feature toggle decorators and utilities for protecting views based on feature toggles.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from invoicing_app.core.models import CompanySettings


def require_feature(feature_name):
    """
    Decorator to protect views based on feature toggles.
    
    Usage:
        @require_feature('payments')
        def payments_list(request):
            ...
        
        @require_feature('export')
        def export_pdf(request):
            ...
    
    Args:
        feature_name: 'payments', 'reminders', or 'export'
    
    Returns:
        Decorated view function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            settings = CompanySettings.get_settings()
            
            # Check if feature is enabled
            if not settings.is_feature_enabled(feature_name):
                feature_label = feature_name.replace('_', ' ').title()
                messages.error(
                    request, 
                    f'{feature_label} is currently disabled by your administrator'
                )
                return redirect('core:dashboard')
            
            # Feature is enabled, proceed with view
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def is_feature_enabled(feature_name):
    """
    Check if a feature is enabled.
    
    Usage:
        if is_feature_enabled('export'):
            # Show export buttons
    
    Args:
        feature_name: 'payments', 'reminders', or 'export'
    
    Returns:
        Boolean indicating if feature is enabled
    """
    settings = CompanySettings.get_settings()
    return settings.is_feature_enabled(feature_name)
