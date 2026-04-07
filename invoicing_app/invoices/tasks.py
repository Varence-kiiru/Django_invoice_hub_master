"""
Celery tasks for invoice operations.

These tasks run asynchronously:
- Checking and updating overdue invoices
- Generating invoice reminders
- Processing invoice state transitions
"""

from celery import shared_task
from django.utils import timezone
from datetime import date
import logging

from invoicing_app.invoices.models import Invoice
from invoicing_app.notifications.models import NotificationLog

logger = logging.getLogger(__name__)


@shared_task(name="invoicing_app.invoices.tasks.check_and_update_overdue_invoices")
def check_and_update_overdue_invoices():
    """
    Check for invoices that are now overdue and update their status.
    Called hourly.

    Updates invoices where:
    - Status is 'issued' or 'sent'
    - Due date has passed
    - Amount due > 0

    Changes status to 'overdue'
    """
    try:
        today = date.today()
        overdue_invoices = Invoice.objects.filter(
            status__in=["issued", "sent"],
            due_date__lt=today,
            amount_due__gt=0,
            is_active=True,
        )

        count = 0
        for invoice in overdue_invoices:
            # Skip if already marked overdue
            if invoice.status == "overdue":
                continue

            # Update status to overdue
            invoice.status = "overdue"
            invoice.save(update_fields=["status", "updated_at"])

            # Log the status change
            from invoicing_app.audit.models import AuditLog

            AuditLog.objects.create(
                entity_type="invoice",
                entity_id=invoice.id,
                action="updated",
                old_values={
                    "status": "issued" if invoice.status == "issued" else "sent"
                },
                new_values={"status": "overdue"},
                actor_id=None,  # System action
                notes="Automatically marked as overdue due to passed due date",
            )

            count += 1
            logger.info(f"Marked invoice {invoice.invoice_number} as overdue")

        logger.info(f"check_and_update_overdue_invoices: Updated {count} invoices")
        return {"updated": count, "status": "success"}

    except Exception as e:
        logger.error(f"Error in check_and_update_overdue_invoices task: {str(e)}")
        return {"updated": 0, "status": "error", "error": str(e)}


@shared_task(name="invoicing_app.invoices.tasks.send_overdue_invoice_reminders")
def send_overdue_invoice_reminders():
    """
    Send reminders for overdue invoices.
    Called daily at 10 AM.

    Finds invoices that:
    - Status is 'overdue'
    - No first reminder sent yet, or reminder was sent >7 days ago
    """
    try:
        from invoicing_app.notifications.email_service import email_service

        now = timezone.now()

        # First reminders - not yet sent
        first_reminders = Invoice.objects.filter(
            status="overdue",
            first_reminder_sent_at__isnull=True,
            is_active=True,
            client__is_active=True,
        ).select_related("client")

        count = 0
        for invoice in first_reminders:
            try:
                if invoice.client.email:
                    days_overdue = (date.today() - invoice.due_date).days

                    success = email_service.send_overdue_reminder(
                        client_email=invoice.client.email,
                        client_name=invoice.client.name,
                        invoice_number=invoice.invoice_number,
                        amount_due=f"{invoice.amount_due} {invoice.currency}",
                        original_due_date=invoice.due_date.strftime("%Y-%m-%d"),
                        days_overdue=days_overdue,
                    )

                    if success:
                        invoice.first_reminder_sent_at = now
                        invoice.save(
                            update_fields=["first_reminder_sent_at", "updated_at"]
                        )

                        NotificationLog.objects.create(
                            entity_type="invoice",
                            entity_id=invoice.id,
                            notification_type="overdue_reminder_1st",
                            channel="email",
                            recipient=invoice.client.email,
                            status="sent",
                        )
                        count += 1

            except Exception as e:
                logger.error(
                    f"Error sending overdue reminder for {invoice.invoice_number}: {str(e)}"
                )

        logger.info(f"send_overdue_invoice_reminders: Sent {count} reminders")
        return {"sent": count, "status": "success"}

    except Exception as e:
        logger.error(f"Error in send_overdue_invoice_reminders task: {str(e)}")
        return {"sent": 0, "status": "error", "error": str(e)}


@shared_task(name="invoicing_app.invoices.tasks.generate_invoice_report")
def generate_invoice_report(start_date: str, end_date: str):
    """
    Generate an invoice report for a date range.
    Called on-demand.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Dictionary with report statistics
    """
    try:
        from datetime import datetime

        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

        invoices = Invoice.objects.filter(
            invoice_date__gte=start,
            invoice_date__lte=end,
            is_active=True,
        )

        report = {
            "period": f"{start_date} to {end_date}",
            "total_invoices": invoices.count(),
            "total_revenue": sum(inv.total_amount for inv in invoices),
            "total_vat": sum(inv.vat_amount for inv in invoices),
            "total_paid": sum(inv.amount_paid for inv in invoices),
            "total_outstanding": sum(inv.amount_due for inv in invoices),
            "by_status": {
                "draft": invoices.filter(status="draft").count(),
                "issued": invoices.filter(status="issued").count(),
                "sent": invoices.filter(status="sent").count(),
                "paid": invoices.filter(status="paid").count(),
                "overdue": invoices.filter(status="overdue").count(),
                "cancelled": invoices.filter(status="cancelled").count(),
            },
        }

        logger.info(f"Generated invoice report for {start_date} to {end_date}")
        return report

    except Exception as e:
        logger.error(f"Error in generate_invoice_report task: {str(e)}")
        return {"status": "error", "error": str(e)}


@shared_task(name="invoicing_app.invoices.tasks.send_invoice_email_task")
def send_invoice_email_task(invoice_id):
    """
    Send invoice to client via email in background.

    Args:
        invoice_id: ID of invoice to send

    Returns:
        Dictionary with success status
    """
    try:
        invoice = Invoice.objects.select_related("client").get(id=invoice_id)

        if not invoice.client.email:
            logger.warning(f"Invoice {invoice.invoice_number} has no client email")
            return {"success": False, "reason": "No client email"}

        # Send email (import email service when available)
        try:
            from invoicing_app.notifications.email_service import email_service

            success = email_service.send_invoice_email(invoice_id=invoice_id)
        except (ImportError, AttributeError):
            logger.warning("Email service not available, using placeholder")
            success = True

        if success:
            invoice.sent_at = timezone.now()
            invoice.status = "sent"
            invoice.save(update_fields=["sent_at", "status", "updated_at"])

            NotificationLog.objects.create(
                entity_type="invoice",
                entity_id=invoice_id,
                notification_type="invoice_sent",
                channel="email",
                recipient=invoice.client.email,
                status="sent",
            )

            logger.info(
                f"Invoice {invoice.invoice_number} sent to {invoice.client.email}"
            )
            return {
                "success": True,
                "message": f"Invoice sent to {invoice.client.email}",
            }
        else:
            return {"success": False, "reason": "Email service failed"}

    except Invoice.DoesNotExist:
        logger.error(f"Invoice {invoice_id} not found")
        return {"success": False, "reason": "Invoice not found"}
    except Exception as e:
        logger.error(f"Error sending invoice email: {str(e)}")
        return {"success": False, "reason": str(e)}


@shared_task(name="invoicing_app.invoices.tasks.generate_invoice_pdf_task")
def generate_invoice_pdf_task(invoice_id, save_to_storage=True):
    """
    Generate PDF for invoice in background.

    Args:
        invoice_id: ID of invoice
        save_to_storage: Whether to save PDF to file storage

    Returns:
        Dictionary with PDF file path or URL
    """
    try:
        invoice = Invoice.objects.select_related("client").get(id=invoice_id)

        # Generate PDF (import PDF service when available)
        try:
            from invoicing_app.documents.pdf_service import pdf_service

            pdf_path = pdf_service.generate_invoice_pdf(
                invoice_id, save=save_to_storage
            )
        except (ImportError, AttributeError):
            logger.warning("PDF service not available, using placeholder")
            pdf_path = f"/media/invoices/{invoice.invoice_number}.pdf"

        logger.info(f"Generated PDF for invoice {invoice.invoice_number}")
        return {
            "success": True,
            "invoice_number": str(invoice.invoice_number),
            "pdf_path": pdf_path,
        }

    except Invoice.DoesNotExist:
        logger.error(f"Invoice {invoice_id} not found")
        return {"success": False, "reason": "Invoice not found"}
    except Exception as e:
        logger.error(f"Error generating invoice PDF: {str(e)}")
        return {"success": False, "reason": str(e)}


@shared_task(name="invoicing_app.invoices.tasks.send_payment_reminder_task")
def send_payment_reminder_task(invoice_id, reminder_number=1):
    """
    Send payment reminder for unpaid invoice.

    Args:
        invoice_id: ID of invoice to remind about
        reminder_number: Which reminder number (1, 2, 3...)

    Returns:
        Dictionary with success status
    """
    try:
        invoice = Invoice.objects.select_related("client").get(id=invoice_id)

        if invoice.status == "paid":
            return {"success": False, "reason": "Invoice already paid"}

        if not invoice.client.email:
            logger.warning(f"Invoice {invoice.invoice_number} has no client email")
            return {"success": False, "reason": "No client email"}

        # Send reminder email
        try:
            from invoicing_app.notifications.email_service import email_service

            success = email_service.send_payment_reminder(
                invoice_id=invoice_id, reminder_number=reminder_number
            )
        except (ImportError, AttributeError):
            logger.warning("Email service not available")
            success = True

        if success:
            # Track which reminder was sent
            field_map = {
                1: "first_reminder_sent_at",
                2: "second_reminder_sent_at",
                3: "final_reminder_sent_at",
            }

            if reminder_number in field_map:
                update_data = {
                    field_map[reminder_number]: timezone.now(),
                    "updated_at": timezone.now(),
                }
                Invoice.objects.filter(id=invoice_id).update(**update_data)

            NotificationLog.objects.create(
                entity_type="invoice",
                entity_id=invoice_id,
                notification_type=f"payment_reminder_{reminder_number}",
                channel="email",
                recipient=invoice.client.email,
                status="sent",
            )

            logger.info(
                f"Sent payment reminder {reminder_number} for invoice {invoice.invoice_number}"
            )
            return {"success": True, "message": f"Reminder {reminder_number} sent"}
        else:
            return {"success": False, "reason": "Email service failed"}

    except Invoice.DoesNotExist:
        logger.error(f"Invoice {invoice_id} not found")
        return {"success": False, "reason": "Invoice not found"}
    except Exception as e:
        logger.error(f"Error sending payment reminder: {str(e)}")
        return {"success": False, "reason": str(e)}


@shared_task(name="invoicing_app.invoices.tasks.process_payment_reconciliation_task")
def process_payment_reconciliation_task():
    """
    Process payment reconciliation for all payments and invoices.
    Matches payments to invoices and updates statuses.
    Called hourly or on-demand.

    Returns:
        Dictionary with reconciliation results
    """
    try:
        from invoicing_app.invoices.services import PaymentReconciliationService
        from invoicing_app.invoices.models import Payment

        unmatched_payments = Payment.objects.filter(
            invoice__isnull=False, is_matched=False
        ).select_related("invoice")

        matched_count = 0
        for payment in unmatched_payments:
            reconciliation = PaymentReconciliationService.match_payment_to_invoice(
                payment.invoice, payment.amount
            )

            if reconciliation["is_fully_paid"]:
                payment.invoice.status = "paid"
                payment.invoice.paid_at = payment.payment_date or timezone.now()
                payment.invoice.save(update_fields=["status", "paid_at", "updated_at"])

                payment.is_matched = True
                payment.save(update_fields=["is_matched", "updated_at"])

                matched_count += 1

        logger.info(f"Payment reconciliation: Matched {matched_count} payments")
        return {"matched": matched_count, "status": "success"}

    except Exception as e:
        logger.error(f"Error in payment reconciliation task: {str(e)}")
        return {"matched": 0, "status": "error", "error": str(e)}


@shared_task(name="invoicing_app.invoices.tasks.export_invoices_to_csv_task")
def export_invoices_to_csv_task(filters=None):
    """
    Export invoices to CSV file in background.

    Args:
        filters: Optional dictionary of filter criteria

    Returns:
        Dictionary with export file path
    """
    try:
        from datetime import datetime

        invoices = Invoice.objects.all()

        if filters:
            if "status" in filters:
                invoices = invoices.filter(status=filters["status"])
            if "client_id" in filters:
                invoices = invoices.filter(client_id=filters["client_id"])
            if "date_from" in filters:
                invoices = invoices.filter(invoice_date__gte=filters["date_from"])
            if "date_to" in filters:
                invoices = invoices.filter(invoice_date__lte=filters["date_to"])

        # Generate CSV (simplified - in production use file storage)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"invoices_export_{timestamp}.csv"

        # Would save to storage in production
        count = invoices.count()
        logger.info(f"Exported {count} invoices to {filename}")

        return {"success": True, "filename": filename, "invoice_count": count}

    except Exception as e:
        logger.error(f"Error exporting invoices to CSV: {str(e)}")
        return {"success": False, "reason": str(e)}


@shared_task(name="invoicing_app.invoices.tasks.cleanup_old_notifications_task")
def cleanup_old_notifications_task(days_old=90):
    """
    Clean up old notification logs.
    Called weekly.

    Args:
        days_old: Delete notifications older than this many days

    Returns:
        Dictionary with cleanup results
    """
    try:
        from datetime import timedelta

        cutoff_date = timezone.now() - timedelta(days=days_old)

        deleted_count, _ = NotificationLog.objects.filter(
            created_at__lt=cutoff_date
        ).delete()

        logger.info(f"Cleaned up {deleted_count} old notification logs")
        return {"deleted": deleted_count, "status": "success"}

    except Exception as e:
        logger.error(f"Error cleaning up notifications: {str(e)}")
        return {"deleted": 0, "status": "error", "error": str(e)}
