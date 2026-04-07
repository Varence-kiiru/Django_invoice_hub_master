"""
Signal handlers for invoice app.
Handles automation for invoice creation, payment processing, and status changes.
"""

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.files.storage import default_storage
from django.db import transaction
import logging

from invoicing_app.invoices.models import Invoice, InvoiceLineItem
from invoicing_app.payments.models import Payment
from invoicing_app.audit.models import AuditLog
from invoicing_app.audit.signals import create_invoice_snapshot
from invoicing_app.invoices.services import PaymentReconciliationService

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Invoice)
def track_invoice_status_change(sender, instance, **kwargs):
    """
    Track status changes for audit purposes.
    Store the old status to detect transitions.
    Also clears cached PDF if status or critical fields change.
    """
    try:
        old_instance = Invoice.objects.get(pk=instance.pk)

        # Check if status changed
        if old_instance.status != instance.status:
            instance._old_status = old_instance.status
            instance._status_changed = True
            # Clear PDF cache when status changes
            _clear_invoice_pdf_cache(old_instance)
        else:
            instance._status_changed = False

        # Check if other critical fields changed (due date, amount, etc.)
        fields_to_check = ["due_date", "description", "total_amount"]
        for field in fields_to_check:
            if getattr(old_instance, field) != getattr(instance, field):
                # Clear PDF cache if any critical field changes
                _clear_invoice_pdf_cache(old_instance)
                break

        # Also clear if amount_paid changed (affects payment status display)
        if old_instance.amount_paid != instance.amount_paid:
            _clear_invoice_pdf_cache(old_instance)

    except Invoice.DoesNotExist:
        instance._status_changed = False


def _clear_invoice_pdf_cache(invoice):
    """Helper function to clear cached PDF for an invoice.
    Defers the save operation until after the current transaction completes
    to avoid transaction management errors.
    """
    if invoice.invoice_pdf:
        try:
            if default_storage.exists(invoice.invoice_pdf.name):
                default_storage.delete(invoice.invoice_pdf.name)

            # Defer the database save until after the transaction completes
            def clear_pdf_field():
                try:
                    invoice.invoice_pdf = None
                    invoice.save(update_fields=["invoice_pdf"])
                    logger.info(
                        f"Cleared cached PDF for invoice {invoice.invoice_number}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Error clearing PDF field for invoice {invoice.invoice_number}: {str(e)}"
                    )

            transaction.on_commit(clear_pdf_field)

        except Exception as e:
            logger.warning(
                f"Error clearing PDF cache for invoice {invoice.invoice_number}: {str(e)}"
            )


@receiver(post_save, sender=Invoice)
def invoice_post_save(sender, instance, created, **kwargs):
    """
    Handle invoice creation and status changes.
    1. Create audit log entry when invoice is created
    2. Create immutable snapshot when invoice is issued
    3. Log all status transitions
    """
    if created:
        # Create audit log for creation
        AuditLog.objects.create(
            entity_type="invoice",
            entity_id=instance.id,
            action="created",
            notes=f"Invoice {instance.invoice_number} created for {instance.client.name}",
            old_values={},
            new_values={
                "invoice_number": str(instance.invoice_number),
                "client": str(instance.client),
                "total_amount": str(instance.total_amount),
                "status": instance.status,
            },
            actor=getattr(instance, "_changed_by", None),
        )

    # When invoice is issued, create immutable snapshot
    if instance.status == "issued":
        create_invoice_snapshot(instance)

    # Log status changes
    if hasattr(instance, "_status_changed") and instance._status_changed:
        old_status = getattr(instance, "_old_status", None)
        new_status = instance.status

        AuditLog.objects.create(
            entity_type="invoice",
            entity_id=instance.id,
            action="status_changed",
            notes=f"Invoice {instance.invoice_number} status changed from {old_status} to {new_status}",
            old_values={"status": old_status},
            new_values={"status": new_status},
            actor=getattr(instance, "_changed_by", None),
        )


@receiver(post_save, sender=Payment)
def handle_payment_created(sender, instance, created, **kwargs):
    """
    When payment is created:
    1. Create audit log entry
    2. Check if invoice is fully paid
    3. Update invoice status to paid if amount fully satisfies invoice
    """
    if created:
        # Create audit log
        AuditLog.objects.create(
            entity_type="payment",
            entity_id=instance.id,
            action="created",
            notes=f"Payment of ${instance.amount:.2f} received for invoice {instance.invoice.invoice_number}",
            old_values={},
            new_values={
                "invoice": str(instance.invoice),
                "amount": str(instance.amount),
                "payment_method": (
                    instance.payment_method.name if instance.payment_method else None
                ),
            },
            actor=getattr(instance, "_changed_by", None),
        )

        # Check if payment fully satisfies invoice
        invoice = instance.invoice
        reconciliation = PaymentReconciliationService.match_payment_to_invoice(
            invoice, instance.amount
        )

        # Update invoice status to paid if fully satisfied
        if reconciliation["is_fully_paid"]:
            invoice.status = "paid"
            invoice.paid_at = instance.payment_date or timezone.now()
            invoice.save(update_fields=["status", "paid_at"])

            # Create audit log for status change
            AuditLog.objects.create(
                entity_type="invoice",
                entity_id=invoice.id,
                action="marked_paid",
                notes=f"Invoice {invoice.invoice_number} marked as paid from payment",
                old_values={"status": "issued"},
                new_values={"status": "paid"},
                actor=getattr(instance, "_changed_by", None),
            )


@receiver(post_save, sender=InvoiceLineItem)
def handle_line_item_change(sender, instance, created, **kwargs):
    """
    When line item is created or changed, recalculate invoice totals.
    This ensures invoice total_amount stays in sync with line items.
    """
    invoice = instance.invoice

    # Recalculate invoice totals from all line items
    line_items = invoice.line_items.all()
    subtotal = sum(item.line_amount for item in line_items)
    vat_total = sum(item.tax_amount or 0 for item in line_items)

    invoice.subtotal_amount = subtotal
    invoice.vat_amount = vat_total
    invoice.total_amount = subtotal + vat_total
    invoice.amount_due = invoice.total_amount - (invoice.amount_paid or 0)
    invoice.save(
        update_fields=["subtotal_amount", "vat_amount", "total_amount", "amount_due"]
    )


@receiver(post_delete, sender=InvoiceLineItem)
def handle_line_item_deleted(sender, instance, **kwargs):
    """
    When line item is deleted, recalculate invoice totals.
    Ensures invoice amounts stay consistent even after deletion.
    """
    invoice = instance.invoice

    # Recalculate invoice totals after deletion
    line_items = invoice.line_items.all()
    subtotal = sum(item.line_amount for item in line_items)
    vat_total = sum(item.tax_amount or 0 for item in line_items)

    invoice.subtotal_amount = subtotal
    invoice.vat_amount = vat_total
    invoice.total_amount = subtotal + vat_total
    invoice.amount_due = invoice.total_amount - (invoice.amount_paid or 0)
    invoice.save(
        update_fields=["subtotal_amount", "vat_amount", "total_amount", "amount_due"]
    )
