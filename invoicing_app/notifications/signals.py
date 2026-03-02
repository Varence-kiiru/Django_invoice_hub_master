"""
Notification signal handlers for logging and event tracking.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from invoicing_app.invoices.models import Invoice
from invoicing_app.payments.models import Payment
from invoicing_app.notifications.models import NotificationLog


@receiver(post_save, sender=Invoice)
def invoice_status_changed_notification(sender, instance, created, **kwargs):
    """
    Log invoice status change as a notification event.
    Handles: issued, sent, viewed, overdue, paid, cancelled
    """
    if created:
        # Log invoice created
        log_notification(
            entity_type='invoice',
            entity_id=instance.id,
            notification_type='invoice_created',
            recipient=instance.client.email if instance.client.email else 'N/A',
            subject=f'Invoice {instance.invoice_number} created'
        )
    else:
        # Log status change
        if instance.status == 'issued':
            log_notification(
                entity_type='invoice',
                entity_id=instance.id,
                notification_type='invoice_issued',
                recipient=instance.client.email if instance.client.email else 'N/A',
                subject=f'Invoice {instance.invoice_number} has been issued'
            )
        elif instance.status == 'sent':
            log_notification(
                entity_type='invoice',
                entity_id=instance.id,
                notification_type='invoice_sent',
                recipient=instance.client.email if instance.client.email else 'N/A',
                subject=f'Invoice {instance.invoice_number} sent to you'
            )
        elif instance.status == 'viewed':
            log_notification(
                entity_type='invoice',
                entity_id=instance.id,
                notification_type='invoice_viewed',
                recipient=instance.client.email if instance.client.email else 'N/A',
                subject=f'Invoice {instance.invoice_number} viewed'
            )
        elif instance.status == 'paid':
            log_notification(
                entity_type='invoice',
                entity_id=instance.id,
                notification_type='invoice_paid',
                recipient=instance.client.email if instance.client.email else 'N/A',
                subject=f'Invoice {instance.invoice_number} marked as paid'
            )
        elif instance.status == 'overdue':
            log_notification(
                entity_type='invoice',
                entity_id=instance.id,
                notification_type='invoice_overdue',
                recipient=instance.client.email if instance.client.email else 'N/A',
                subject=f'Invoice {instance.invoice_number} is now overdue'
            )
        elif instance.status == 'cancelled':
            log_notification(
                entity_type='invoice',
                entity_id=instance.id,
                notification_type='invoice_cancelled',
                recipient=instance.client.email if instance.client.email else 'N/A',
                subject=f'Invoice {instance.invoice_number} has been cancelled'
            )


@receiver(post_save, sender=Payment)
def payment_received_notification(sender, instance, created, **kwargs):
    """
    Log payment events when payments are recorded.
    """
    if created:
        log_notification(
            entity_type='payment',
            entity_id=instance.id,
            notification_type='payment_received',
            recipient=instance.invoice.client.email if instance.invoice.client.email else 'N/A',
            subject=f'Payment of {instance.amount} recorded for {instance.invoice.invoice_number}'
        )
    
    # Log when payment is confirmed
    if instance.status == 'confirmed':
        log_notification(
            entity_type='payment',
            entity_id=instance.id,
            notification_type='payment_confirmed',
            recipient=instance.invoice.client.email if instance.invoice.client.email else 'N/A',
            subject=f'Payment of {instance.amount} for {instance.invoice.invoice_number} confirmed'
        )
    elif instance.status == 'failed':
        log_notification(
            entity_type='payment',
            entity_id=instance.id,
            notification_type='payment_failed',
            recipient=instance.invoice.client.email if instance.invoice.client.email else 'N/A',
            subject=f'Payment of {instance.amount} for {instance.invoice.invoice_number} failed'
        )


def log_notification(entity_type, entity_id, notification_type, recipient, subject):
    """
    Helper to create a NotificationLog entry.
    """
    try:
        NotificationLog.objects.create(
            entity_type=entity_type,
            entity_id=entity_id,
            notification_type=notification_type,
            recipient=recipient,
            subject=subject,
            status='pending',
        )
    except Exception:
        # Silently fail if NotificationLog table doesn't exist
        pass
