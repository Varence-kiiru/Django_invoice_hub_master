"""
Notification signal handlers for logging and event tracking.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from invoicing_app.invoices.models import Invoice
from invoicing_app.payments.models import Payment
from invoicing_app.quotations.models import Quote
from invoicing_app.deliveries.models import Delivery
from invoicing_app.expenses.models import Expense
from invoicing_app.organizations.models import OrganizationMember
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
            entity_type="invoice",
            entity_id=instance.id,
            notification_type="invoice_created",
            recipient=instance.client.email if instance.client.email else "N/A",
            subject=f"Invoice {instance.invoice_number} created",
        )
    else:
        # Log status change
        if instance.status == "issued":
            log_notification(
                entity_type="invoice",
                entity_id=instance.id,
                notification_type="invoice_issued",
                recipient=instance.client.email if instance.client.email else "N/A",
                subject=f"Invoice {instance.invoice_number} has been issued",
            )
        elif instance.status == "sent":
            log_notification(
                entity_type="invoice",
                entity_id=instance.id,
                notification_type="invoice_sent",
                recipient=instance.client.email if instance.client.email else "N/A",
                subject=f"Invoice {instance.invoice_number} sent to you",
            )
        elif instance.status == "viewed":
            log_notification(
                entity_type="invoice",
                entity_id=instance.id,
                notification_type="invoice_viewed",
                recipient=instance.client.email if instance.client.email else "N/A",
                subject=f"Invoice {instance.invoice_number} viewed",
            )
        elif instance.status == "paid":
            log_notification(
                entity_type="invoice",
                entity_id=instance.id,
                notification_type="invoice_paid",
                recipient=instance.client.email if instance.client.email else "N/A",
                subject=f"Invoice {instance.invoice_number} marked as paid",
            )
        elif instance.status == "overdue":
            log_notification(
                entity_type="invoice",
                entity_id=instance.id,
                notification_type="invoice_overdue",
                recipient=instance.client.email if instance.client.email else "N/A",
                subject=f"Invoice {instance.invoice_number} is now overdue",
            )
        elif instance.status == "cancelled":
            log_notification(
                entity_type="invoice",
                entity_id=instance.id,
                notification_type="invoice_cancelled",
                recipient=instance.client.email if instance.client.email else "N/A",
                subject=f"Invoice {instance.invoice_number} has been cancelled",
            )


@receiver(post_save, sender=Payment)
def payment_received_notification(sender, instance, created, **kwargs):
    """
    Log payment events when payments are recorded.
    """
    if created:
        log_notification(
            entity_type="payment",
            entity_id=instance.id,
            notification_type="payment_received",
            recipient=(
                instance.invoice.client.email
                if instance.invoice.client.email
                else "N/A"
            ),
            subject=f"Payment of {instance.amount} recorded for {instance.invoice.invoice_number}",
        )

    # Log when payment is confirmed
    if instance.status == "confirmed":
        log_notification(
            entity_type="payment",
            entity_id=instance.id,
            notification_type="payment_confirmed",
            recipient=(
                instance.invoice.client.email
                if instance.invoice.client.email
                else "N/A"
            ),
            subject=f"Payment of {instance.amount} for {instance.invoice.invoice_number} confirmed",
        )
    elif instance.status == "failed":
        log_notification(
            entity_type="payment",
            entity_id=instance.id,
            notification_type="payment_failed",
            recipient=(
                instance.invoice.client.email
                if instance.invoice.client.email
                else "N/A"
            ),
            subject=f"Payment of {instance.amount} for {instance.invoice.invoice_number} failed",
        )


# QUOTATION SIGNALS
@receiver(post_save, sender=Quote)
def quote_status_changed_notification(sender, instance, created, **kwargs):
    """Log quotation status changes."""
    if created:
        log_notification(
            entity_type="quotation",
            entity_id=instance.id,
            notification_type="quote_created",
            recipient=instance.client.email if instance.client.email else "N/A",
            subject=f"Quotation {instance.quote_number} created",
        )
    else:
        if instance.status == "issued":
            log_notification(
                entity_type="quotation",
                entity_id=instance.id,
                notification_type="quote_issued",
                recipient=instance.client.email if instance.client.email else "N/A",
                subject=f"Quotation {instance.quote_number} issued",
            )
        elif instance.status == "accepted":
            log_notification(
                entity_type="quotation",
                entity_id=instance.id,
                notification_type="quote_accepted",
                recipient=instance.client.email if instance.client.email else "N/A",
                subject=f"Quotation {instance.quote_number} accepted",
            )
        elif instance.status == "rejected":
            log_notification(
                entity_type="quotation",
                entity_id=instance.id,
                notification_type="quote_rejected",
                recipient=instance.client.email if instance.client.email else "N/A",
                subject=f"Quotation {instance.quote_number} rejected",
            )
        elif instance.status == "converted":
            log_notification(
                entity_type="quotation",
                entity_id=instance.id,
                notification_type="quote_converted",
                recipient=instance.client.email if instance.client.email else "N/A",
                subject=f"Quotation {instance.quote_number} converted to invoice",
            )


# DELIVERY SIGNALS
@receiver(post_save, sender=Delivery)
def delivery_status_changed_notification(sender, instance, created, **kwargs):
    """Log delivery status changes."""
    if created:
        log_notification(
            entity_type="delivery",
            entity_id=instance.id,
            notification_type="delivery_created",
            recipient=(
                instance.invoice.client.email
                if instance.invoice.client.email
                else "N/A"
            ),
            subject=f"Delivery {instance.delivery_number} created for invoice {instance.invoice.invoice_number}",
        )
    else:
        if instance.status == "pending":
            log_notification(
                entity_type="delivery",
                entity_id=instance.id,
                notification_type="delivery_pending",
                recipient=(
                    instance.invoice.client.email
                    if instance.invoice.client.email
                    else "N/A"
                ),
                subject=f"Delivery {instance.delivery_number} is pending",
            )
        elif instance.status == "in_transit":
            log_notification(
                entity_type="delivery",
                entity_id=instance.id,
                notification_type="delivery_in_transit",
                recipient=(
                    instance.invoice.client.email
                    if instance.invoice.client.email
                    else "N/A"
                ),
                subject="Your delivery is on its way!",
            )
        elif instance.status == "delivered":
            log_notification(
                entity_type="delivery",
                entity_id=instance.id,
                notification_type="delivery_completed",
                recipient=(
                    instance.invoice.client.email
                    if instance.invoice.client.email
                    else "N/A"
                ),
                subject=f"Delivery {instance.delivery_number} completed",
            )


# EXPENSE SIGNALS
@receiver(post_save, sender=Expense)
def expense_status_changed_notification(sender, instance, created, **kwargs):
    """Log expense status changes."""
    if created:
        log_notification(
            entity_type="expense",
            entity_id=instance.id,
            notification_type="expense_created",
            recipient=instance.created_by.email if instance.created_by.email else "N/A",
            subject=f"Expense #{instance.id} created - {instance.description}",
        )
    else:
        if instance.status == "pending_approval":
            log_notification(
                entity_type="expense",
                entity_id=instance.id,
                notification_type="expense_pending_approval",
                recipient=(
                    instance.approver.email
                    if instance.approver and instance.approver.email
                    else "N/A"
                ),
                subject=f"Expense approval required - ${instance.amount}",
            )
        elif instance.status == "approved":
            log_notification(
                entity_type="expense",
                entity_id=instance.id,
                notification_type="expense_approved",
                recipient=(
                    instance.created_by.email if instance.created_by.email else "N/A"
                ),
                subject=f"Your expense has been approved - ${instance.amount}",
            )
        elif instance.status == "rejected":
            log_notification(
                entity_type="expense",
                entity_id=instance.id,
                notification_type="expense_rejected",
                recipient=(
                    instance.created_by.email if instance.created_by.email else "N/A"
                ),
                subject="Your expense has been rejected",
            )


# TEAM MEMBER SIGNALS
@receiver(post_save, sender=OrganizationMember)
def team_member_notification(sender, instance, created, **kwargs):
    """Log team member activities."""
    if created:
        log_notification(
            entity_type="team_member",
            entity_id=instance.id,
            notification_type="member_invited",
            recipient=instance.user.email if instance.user.email else "N/A",
            subject=f"You've been added to {instance.organization.name}",
        )
    else:
        if instance.status == "active":
            log_notification(
                entity_type="team_member",
                entity_id=instance.id,
                notification_type="member_activated",
                recipient=instance.user.email if instance.user.email else "N/A",
                subject=f"Your membership in {instance.organization.name} is now active",
            )
        elif instance.status == "inactive":
            log_notification(
                entity_type="team_member",
                entity_id=instance.id,
                notification_type="member_deactivated",
                recipient=instance.user.email if instance.user.email else "N/A",
                subject=f"Your membership in {instance.organization.name} has been deactivated",
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
            status="pending",
        )
    except Exception:
        # Silently fail if NotificationLog table doesn't exist
        pass
