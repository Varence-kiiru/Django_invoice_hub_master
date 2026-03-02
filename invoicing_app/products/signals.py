"""
Signal handlers for products app.
Handles product-related automation and audit logging.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from invoicing_app.products.models import Product
from invoicing_app.audit.models import AuditLog


@receiver(post_save, sender=Product)
def handle_product_created_or_modified(sender, instance, created, **kwargs):
    """
    Create audit log when product is created.
    """
    if created:
        AuditLog.objects.create(
            entity_type='product',
            entity_id=instance.id,
            action='created',
            notes=f'Product {instance.name} created with SKU {instance.sku}',
            old_values={},
            new_values={
                'name': instance.name,
                'sku': instance.sku,
                'unit_price': str(instance.unit_price),
                'category': str(instance.category) if instance.category else None,
                'is_active': instance.is_active,
            },
            actor=getattr(instance, '_changed_by', None),
        )


@receiver(pre_save, sender=Product)
def track_product_changes(sender, instance, **kwargs):
    """
    Track product field changes for audit purposes.
    """
    if instance.pk:
        try:
            old_instance = Product.objects.get(pk=instance.pk)
            changes = {}
            
            # Track important fields
            for field in ['name', 'unit_price', 'category', 'is_active']:
                old_val = getattr(old_instance, field)
                new_val = getattr(instance, field)
                if old_val != new_val:
                    changes[field] = {
                        'old': str(old_val),
                        'new': str(new_val)
                    }
            
            if changes:
                instance._changes = changes
        except Product.DoesNotExist:
            pass


@receiver(post_save, sender=Product)
def log_product_changes(sender, instance, created, **kwargs):
    """
    Log tracked changes to audit log.
    """
    if not created and hasattr(instance, '_changes'):
        changes = instance._changes
        AuditLog.objects.create(
            entity_type='product',
            entity_id=instance.id,
            action='updated',
            notes=f'Product {instance.name} updated: {", ".join(changes.keys())}',
            old_values={k: v['old'] for k, v in changes.items()},
            new_values={k: v['new'] for k, v in changes.items()},
            actor=getattr(instance, '_changed_by', None),
        )
