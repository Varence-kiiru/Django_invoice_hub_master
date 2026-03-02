from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from invoicing_app.audit.models import AuditLog, InvoiceSnapshot


@receiver(post_save)
def create_audit_log_on_save(sender, instance, created, **kwargs):
    # Only create audit entries for our app models to avoid recording Django internals
    try:
        app_label = sender._meta.app_label
    except Exception:
        return
    if not app_label.startswith('invoicing_app'):
        return

    # Avoid recursion for audit models
    if app_label == 'invoicing_app' and sender.__name__ in ('AuditLog', 'InvoiceSnapshot'):
        return

    action = 'created' if created else 'updated'

    def _sanitize(obj):
        """Recursively sanitize model_to_dict output for JSON storage."""
        from django.db.models import Model
        from django.db.models.fields.files import FieldFile
        
        if isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_sanitize(v) for v in obj]
        # Handle FileField/ImageField (FieldFile objects)
        if isinstance(obj, FieldFile):
            return str(obj.name) if obj.name else None
        # Handle Model instances by converting to their ID or representation
        if isinstance(obj, Model):
            return obj.pk if hasattr(obj, 'pk') else str(obj)
        # datetime/date objects -> isoformat
        from datetime import datetime, date, time
        if isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        # Handle Decimal and other numeric types
        try:
            from decimal import Decimal
            if isinstance(obj, Decimal):
                return float(obj)
        except Exception:
            pass
        # For primitives and JSON-serializable types, return as-is
        if obj is None or isinstance(obj, (bool, int, float, str)):
            return obj
        # Fallback to string for any other non-serializable types
        return str(obj)

    try:
        # Use model_to_dict but convert FK fields to their IDs instead of objects
        new_raw = model_to_dict(instance)
        # Convert any Model instances to their IDs for JSON serialization
        for key, value in list(new_raw.items()):
            if hasattr(value, 'pk') and hasattr(value, '_meta'):
                # This is a Django Model instance (FK relation)
                new_raw[key] = value.pk
        new = _sanitize(new_raw)
    except Exception as e:
        # If model_to_dict fails, fall back to a minimal representation
        new = {'id': getattr(instance, 'id', None) or 0, '__error__': str(e)}

    # Get actor from request context if available
    actor = None
    from django.db import connection
    from django.db.models import signals as model_signals
    
    # Try to get user from the signal's request context
    if hasattr(instance, '_user'):
        actor = instance._user
    # For Invoice models, use created_by or updated_by
    elif sender.__name__ == 'Invoice' and hasattr(instance, 'updated_by'):
        actor = instance.updated_by or instance.created_by
    # For other models with user tracking fields
    elif hasattr(instance, 'created_by') and created:
        actor = instance.created_by
    elif hasattr(instance, 'updated_by') and not created:
        actor = instance.updated_by

    # Use simpler entity type naming (e.g., 'invoice' instead of 'invoicing_app.invoice')
    entity_type = sender.__name__.lower()
    
    AuditLog.objects.create(
        entity_type=entity_type,
        entity_id=getattr(instance, 'id', None) or 0,
        action=action,
        old_values=None,
        new_values=new,
        actor=actor,
    )


@receiver(post_delete)
def create_audit_log_on_delete(sender, instance, **kwargs):
    try:
        app_label = sender._meta.app_label
    except Exception:
        return
    if not app_label.startswith('invoicing_app'):
        return
    if app_label == 'invoicing_app' and sender.__name__ in ('AuditLog', 'InvoiceSnapshot'):
        return
    
    # Get actor from request context if available
    actor = None
    if hasattr(instance, '_user'):
        actor = instance._user
    
    # Use simpler entity type naming
    entity_type = sender.__name__.lower()
    
    AuditLog.objects.create(
        entity_type=entity_type,
        entity_id=getattr(instance, 'id', None) or 0,
        action='deleted',
        old_values=None,
        new_values=None,
        actor=actor,
    )


def create_invoice_snapshot(invoice):
    # create snapshot for invoice if not existing
    try:
        # Sanitize the invoice data for JSON storage
        invoice_data = model_to_dict(invoice)
        # Convert any Model instances to their IDs for JSON serialization
        for key, value in list(invoice_data.items()):
            if hasattr(value, 'pk') and hasattr(value, '_meta'):
                # This is a Django Model instance (FK relation)
                invoice_data[key] = value.pk
        
        # Final sanitization to ensure everything is JSON-serializable
        def _sanitize_for_snapshot(obj):
            from django.db.models import Model
            from django.db.models.fields.files import FieldFile
            from datetime import datetime, date, time
            from decimal import Decimal
            
            if isinstance(obj, dict):
                return {k: _sanitize_for_snapshot(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_sanitize_for_snapshot(v) for v in obj]
            if isinstance(obj, FieldFile):
                return str(obj.name) if obj.name else None
            if isinstance(obj, Model):
                return obj.pk if hasattr(obj, 'pk') else str(obj)
            if isinstance(obj, (datetime, date, time)):
                return obj.isoformat()
            if isinstance(obj, Decimal):
                return float(obj)
            if obj is None or isinstance(obj, (bool, int, float, str)):
                return obj
            return str(obj)
        
        sanitized_data = _sanitize_for_snapshot(invoice_data)
        
        data = {
            'invoice': invoice,
            'invoice_number': invoice.invoice_number,
            'invoice_state_json': sanitized_data,
        }
        InvoiceSnapshot.objects.create(**data)
    except Exception:
        pass
