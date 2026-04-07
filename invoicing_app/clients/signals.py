"""
Signal handlers for clients app.
Handles client-related automation and audit logging.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from invoicing_app.clients.models import Client, ClientAddress, ClientContact
from invoicing_app.audit.models import AuditLog


@receiver(post_save, sender=Client)
def handle_client_created_or_modified(sender, instance, created, **kwargs):
    """
    Create audit log when client is created or modified.
    Provides complete audit trail for client management.
    """
    if created:
        AuditLog.objects.create(
            entity_type="client",
            entity_id=instance.id,
            action="created",
            notes=f"Client {instance.name} created",
            old_values={},
            new_values={
                "name": instance.name,
                "email": instance.email,
                "is_active": instance.is_active,
                "credit_limit": str(instance.credit_limit),
            },
            actor=getattr(instance, "_changed_by", None),
        )


@receiver(pre_save, sender=Client)
def track_client_changes(sender, instance, **kwargs):
    """
    Track client field changes for audit purposes.
    """
    if instance.pk:
        try:
            old_instance = Client.objects.get(pk=instance.pk)
            changes = {}

            # Track important fields
            for field in ["name", "email", "phone", "is_active", "credit_limit"]:
                old_val = getattr(old_instance, field)
                new_val = getattr(instance, field)
                if old_val != new_val:
                    changes[field] = {"old": str(old_val), "new": str(new_val)}

            if changes:
                instance._changes = changes
        except Client.DoesNotExist:
            pass


@receiver(post_save, sender=Client)
def log_client_changes(sender, instance, created, **kwargs):
    """
    Log tracked changes to audit log.
    """
    if not created and hasattr(instance, "_changes"):
        changes = instance._changes
        AuditLog.objects.create(
            entity_type="client",
            entity_id=instance.id,
            action="updated",
            notes=f'Client {instance.name} updated: {", ".join(changes.keys())}',
            old_values={k: v["old"] for k, v in changes.items()},
            new_values={k: v["new"] for k, v in changes.items()},
            actor=getattr(instance, "_changed_by", None),
        )


@receiver(post_save, sender=ClientAddress)
def handle_client_address_changed(sender, instance, created, **kwargs):
    """
    Log when client address is created or modified.
    """
    action = "created" if created else "updated"
    AuditLog.objects.create(
        entity_type="client_address",
        entity_id=instance.id,
        action=action,
        notes=f"Address for client {instance.client.name} {action}",
        old_values={},
        new_values={
            "client": str(instance.client),
            "city": instance.city,
            "country": instance.country,
        },
        actor=getattr(instance, "_changed_by", None),
    )


@receiver(post_save, sender=ClientContact)
def handle_client_contact_changed(sender, instance, created, **kwargs):
    """
    Log when client contact is created or modified.
    """
    action = "created" if created else "updated"
    AuditLog.objects.create(
        entity_type="client_contact",
        entity_id=instance.id,
        action=action,
        notes=f"Contact {instance.name} for client {instance.client.name} {action}",
        old_values={},
        new_values={
            "client": str(instance.client),
            "name": instance.name,
            "email": instance.email,
            "is_primary": instance.is_primary,
        },
        actor=getattr(instance, "_changed_by", None),
    )
