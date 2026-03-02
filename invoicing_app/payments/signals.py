"""
Payment signal handlers for reconciliation and invoice updates.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction, models
from invoicing_app.payments.models import Payment, PaymentReconciliation
from invoicing_app.invoices.models import Invoice
from decimal import Decimal


@receiver(post_save, sender=Payment)
def payment_post_save(sender, instance, created, **kwargs):
    """
    When a payment is saved:
    1. If confirmed, create/update PaymentReconciliation
    2. Update invoice paid amount and due amount
    3. Mark invoice as paid if fully paid
    """
    # Only process confirmed payments
    if instance.status != 'confirmed':
        return
    
    invoice = instance.invoice
    
    # If this is a new confirmed payment, create reconciliation record
    if created:
        PaymentReconciliation.objects.create(
            payment=instance,
            invoice=invoice,
            amount_matched=instance.amount,
        )
    
    # Recalculate invoice paid amount and due amount
    total_paid = invoice.payments.filter(
        status='confirmed'
    ).aggregate(
        total=models.Sum('amount')
    )['total'] or Decimal('0.00')
    
    # Update invoice
    new_amount_paid = total_paid
    new_amount_due = invoice.total_amount - new_amount_paid
    
    with transaction.atomic():
        invoice.amount_paid = new_amount_paid
        invoice.amount_due = new_amount_due
        
        # Auto-mark as paid if fully paid
        if new_amount_due <= Decimal('0.00') and invoice.status != 'paid':
            invoice.status = 'paid'
            invoice.paid_at = timezone.now()  # Set paid timestamp
        
        invoice.save(update_fields=['amount_paid', 'amount_due', 'status', 'paid_at', 'updated_at'])


@receiver(post_delete, sender=Payment)
def payment_post_delete(sender, instance, **kwargs):
    """
    When a payment is deleted:
    1. Update invoice paid amount
    2. Revert invoice status from paid if necessary
    3. Delete associated reconciliation records
    """
    invoice = instance.invoice
    
    # Delete associated reconciliation records (cascaded by model)
    PaymentReconciliation.objects.filter(payment=instance).delete()
    
    # Recalculate invoice paid amount
    total_paid = invoice.payments.filter(
        status='confirmed'
    ).aggregate(
        total=models.Sum('amount')
    )['total'] or Decimal('0.00')
    
    new_amount_paid = total_paid
    new_amount_due = invoice.total_amount - new_amount_paid
    
    with transaction.atomic():
        invoice.amount_paid = new_amount_paid
        invoice.amount_due = new_amount_due
        
        # Revert status from 'paid' if no longer fully paid
        if new_amount_due > Decimal('0.00') and invoice.status == 'paid':
            # Revert to previous status (check due date for overdue status)
            today = timezone.now().date()
            if today > invoice.due_date:
                invoice.status = 'overdue'
            else:
                invoice.status = 'issued'
            invoice.paid_at = None  # Clear paid timestamp
        
        invoice.save(update_fields=['amount_paid', 'amount_due', 'status', 'paid_at', 'updated_at'])


@receiver(post_save, sender=PaymentReconciliation)
def payment_reconciliation_post_save(sender, instance, created, **kwargs):
    """
    When a payment reconciliation is created/updated:
    - Log the reconciliation event
    - Update invoice amount_paid if needed
    """
    if created:
        # Log reconciliation event (handled by audit signals)
        pass


# Import at module level for aggregation
from django.db import models
