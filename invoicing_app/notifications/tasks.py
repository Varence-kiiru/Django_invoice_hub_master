"""
Celery tasks for notification and email operations.

These tasks run asynchronously in the background:
- Sending invoice reminders
- Sending payment reminders
- Cleaning up old notification logs
"""

from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
import logging

from invoicing_app.invoices.models import Invoice
from invoicing_app.deliveries.models import Delivery
from invoicing_app.expenses.models import Expense
from invoicing_app.notifications.models import NotificationLog
from invoicing_app.notifications.email_service import email_service

logger = logging.getLogger(__name__)


@shared_task(name="invoicing_app.notifications.tasks.send_invoice_reminders")
def send_invoice_reminders():
    """
    Send reminders for invoices. Called daily at 9 AM.

    Finds invoices that:
    - Were issued more than 3 days ago
    - Haven't been viewed yet
    - Status is 'issued'
    """
    try:
        from invoicing_app.core.models import CompanySettings

        # Check if reminders feature is enabled
        settings = CompanySettings.get_settings()
        if not settings.enable_reminders:
            logger.info("Invoice reminders are disabled in settings")
            return {"sent": 0, "status": "disabled", "message": "Reminders disabled"}

        three_days_ago = timezone.now() - timedelta(days=3)
        invoices_to_remind = Invoice.objects.filter(
            status="issued",
            viewed_at__isnull=True,
            sent_at__lt=three_days_ago,
            is_active=True,
            client__is_active=True,
        ).select_related("client")

        count = 0
        for invoice in invoices_to_remind:
            try:
                if invoice.client.email:
                    success = email_service.send_invoice_issued_notification(
                        client_email=invoice.client.email,
                        client_name=invoice.client.name,
                        invoice_number=invoice.invoice_number,
                        invoice_date=invoice.invoice_date.strftime("%Y-%m-%d"),
                        total_amount=f"{invoice.total_amount} {invoice.currency}",
                        due_date=invoice.due_date.strftime("%Y-%m-%d"),
                    )

                    if success:
                        # Log the notification
                        NotificationLog.objects.create(
                            entity_type="invoice",
                            entity_id=invoice.id,
                            notification_type="reminder",
                            channel="email",
                            recipient=invoice.client.email,
                            status="sent",
                        )
                        count += 1
                        logger.info(
                            f"Sent reminder for invoice {invoice.invoice_number}"
                        )

            except Exception as e:
                logger.error(
                    f"Error sending reminder for invoice {invoice.invoice_number}: {str(e)}"
                )
                NotificationLog.objects.create(
                    entity_type="invoice",
                    entity_id=invoice.id,
                    notification_type="reminder",
                    channel="email",
                    recipient=(
                        invoice.client.email if invoice.client.email else "unknown"
                    ),
                    status="failed",
                    error_message=str(e),
                )

        logger.info(f"send_invoice_reminders: Sent {count} reminders")
        return {"sent": count, "status": "success"}

    except Exception as e:
        logger.error(f"Error in send_invoice_reminders task: {str(e)}")
        return {"sent": 0, "status": "error", "error": str(e)}


@shared_task(name="invoicing_app.notifications.tasks.send_payment_reminders")
def send_payment_reminders():
    """
    Send reminders for invoices due tomorrow or in 3 days.
    Called daily at 2 PM.

    Finds invoices where:
    - Status is 'issued' or 'sent'
    - Due date is tomorrow or in 3 days
    - Not yet paid
    """
    try:
        from invoicing_app.core.models import CompanySettings

        # Check if reminders feature is enabled
        settings = CompanySettings.get_settings()
        if not settings.enable_reminders:
            logger.info("Payment reminders are disabled in settings")
            return {"sent": 0, "status": "disabled", "message": "Reminders disabled"}

        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        in_three_days = today + timedelta(days=3)

        invoices_to_remind = Invoice.objects.filter(
            Q(due_date=tomorrow) | Q(due_date=in_three_days),
            status__in=["issued", "sent"],
            amount_due__gt=0,
            is_active=True,
            client__is_active=True,
        ).select_related("client")

        count = 0
        for invoice in invoices_to_remind:
            try:
                if invoice.client.email:
                    days_until_due = (invoice.due_date - today).days

                    success = email_service.send_due_soon_reminder(
                        client_email=invoice.client.email,
                        client_name=invoice.client.name,
                        invoice_number=invoice.invoice_number,
                        amount_due=f"{invoice.amount_due} {invoice.currency}",
                        due_date=invoice.due_date.strftime("%Y-%m-%d"),
                        days_until_due=days_until_due,
                    )

                    if success:
                        NotificationLog.objects.create(
                            entity_type="invoice",
                            entity_id=invoice.id,
                            notification_type="payment_reminder",
                            channel="email",
                            recipient=invoice.client.email,
                            status="sent",
                        )
                        count += 1
                        logger.info(
                            f"Sent payment reminder for invoice {invoice.invoice_number}"
                        )

            except Exception as e:
                logger.error(
                    f"Error sending payment reminder for {invoice.invoice_number}: {str(e)}"
                )

        logger.info(f"send_payment_reminders: Sent {count} reminders")
        return {"sent": count, "status": "success"}

    except Exception as e:
        logger.error(f"Error in send_payment_reminders task: {str(e)}")
        return {"sent": 0, "status": "error", "error": str(e)}


@shared_task(name="invoicing_app.notifications.tasks.cleanup_old_notification_logs")
def cleanup_old_notification_logs():
    """
    Clean up notification logs older than 90 days.
    Called weekly on Sunday at midnight.

    Keeps logs for audit trail but removes very old entries.
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=90)
        deleted_count, _ = NotificationLog.objects.filter(
            created_at__lt=cutoff_date
        ).delete()

        logger.info(f"Cleaned up {deleted_count} old notification logs")
        return {"deleted": deleted_count, "status": "success"}

    except Exception as e:
        logger.error(f"Error in cleanup_old_notification_logs task: {str(e)}")
        return {"deleted": 0, "status": "error", "error": str(e)}


@shared_task(name="invoicing_app.notifications.tasks.send_custom_notification")
def send_custom_notification(
    notification_type: str,
    entity_type: str,
    entity_id: int,
    recipient_email: str,
    subject: str,
    html_body: str,
):
    """
    Send a custom notification. Called on-demand.

    Args:
        notification_type: Type of notification (e.g., 'reminder', 'alert')
        entity_type: What entity this is about (e.g., 'invoice', 'payment')
        entity_id: ID of the entity
        recipient_email: Recipient email address
        subject: Email subject
        html_body: HTML email body
    """
    try:
        from django.utils.html import strip_tags

        text_body = strip_tags(html_body)
        success = email_service._send_email(
            subject=subject,
            html_message=html_body,
            text_message=text_body,
            recipient_email=recipient_email,
        )

        if success:
            NotificationLog.objects.create(
                entity_type=entity_type,
                entity_id=entity_id,
                notification_type=notification_type,
                channel="email",
                recipient=recipient_email,
                status="sent",
            )

        return {"sent": success, "status": "success" if success else "failed"}

    except Exception as e:
        logger.error(f"Error in send_custom_notification task: {str(e)}")
        return {"sent": False, "status": "error", "error": str(e)}


@shared_task(name="invoicing_app.notifications.tasks.send_overdue_reminders")
def send_overdue_reminders():
    """
    Send reminders for overdue invoices.
    Called daily at 10 AM.

    Finds invoices that are overdue and sends reminder notifications.
    """
    try:
        from invoicing_app.core.models import CompanySettings

        settings = CompanySettings.get_settings()
        if not settings.enable_reminders:
            return {"sent": 0, "status": "disabled"}

        today = timezone.now().date()
        overdue_invoices = Invoice.objects.filter(
            status__in=["issued", "sent"],
            due_date__lt=today,
            amount_due__gt=0,
            is_active=True,
            client__is_active=True,
        ).select_related("client")

        count = 0
        for invoice in overdue_invoices:
            try:
                if invoice.client.email:
                    days_overdue = (today - invoice.due_date).days
                    email_service.send_overdue_reminder(
                        client_email=invoice.client.email,
                        client_name=invoice.client.name,
                        invoice_number=invoice.invoice_number,
                        amount_due=f"{invoice.amount_due} {invoice.currency}",
                        original_due_date=invoice.due_date.strftime("%Y-%m-%d"),
                        days_overdue=days_overdue,
                    )
                    NotificationLog.objects.create(
                        entity_type="invoice",
                        entity_id=invoice.id,
                        notification_type="overdue_reminder",
                        channel="email",
                        recipient=invoice.client.email,
                        status="sent",
                    )
                    count += 1
                    logger.info(
                        f"Sent overdue reminder for invoice {invoice.invoice_number}"
                    )
            except Exception as e:
                logger.error(
                    f"Error sending overdue reminder for {invoice.invoice_number}: {str(e)}"
                )

        logger.info(f"send_overdue_reminders: Sent {count} reminders")
        return {"sent": count, "status": "success"}
    except Exception as e:
        logger.error(f"Error in send_overdue_reminders: {str(e)}")
        return {"sent": 0, "status": "error"}


@shared_task(name="invoicing_app.notifications.tasks.send_delivery_notifications")
def send_delivery_notifications():
    """
    Send delivery status updates.
    Called every 2 hours.

    Finds in-transit deliveries with expected delivery date today and sends notifications.
    """
    try:
        deliveries = Delivery.objects.filter(
            status="in_transit",
            expected_delivery_date__date=timezone.now().date(),
            is_active=True,
        ).select_related("invoice__client")

        count = 0
        for delivery in deliveries:
            try:
                if delivery.invoice.client.email:
                    email_service.send_delivery_confirmed_notification(
                        client_email=delivery.invoice.client.email,
                        client_name=delivery.invoice.client.name,
                        invoice_number=delivery.invoice.invoice_number,
                        delivery_date=delivery.created_at.strftime("%Y-%m-%d"),
                        expected_arrival=delivery.expected_delivery_date.strftime(
                            "%Y-%m-%d"
                        ),
                    )
                    NotificationLog.objects.create(
                        entity_type="delivery",
                        entity_id=delivery.id,
                        notification_type="delivery_update",
                        channel="email",
                        recipient=delivery.invoice.client.email,
                        status="sent",
                    )
                    count += 1
                    logger.info(
                        f"Sent delivery notification for {delivery.delivery_number}"
                    )
            except Exception as e:
                logger.error(f"Error sending delivery notification: {str(e)}")

        logger.info(f"send_delivery_notifications: Sent {count} notifications")
        return {"sent": count, "status": "success"}
    except Exception as e:
        logger.error(f"Error in send_delivery_notifications: {str(e)}")
        return {"sent": 0, "status": "error"}


@shared_task(name="invoicing_app.notifications.tasks.send_expense_notifications")
def send_expense_notifications():
    """
    Send expense approval reminders.
    Called daily at 11 AM.

    Finds pending expenses created in the last 7 days and sends reminders to approvers.
    """
    try:
        pending_expenses = Expense.objects.filter(
            status="pending_approval",
            approver__isnull=False,
            created_at__gte=timezone.now() - timedelta(days=7),
            is_active=True,
        ).select_related("approver", "created_by")

        count = 0
        for expense in pending_expenses:
            try:
                if expense.approver.email:
                    email_service.send_expense_approval_required(
                        manager_email=expense.approver.email,
                        manager_name=expense.approver.get_full_name(),
                        expense_id=expense.id,
                        amount=str(expense.amount),
                        description=expense.description,
                        submitter_name=expense.created_by.get_full_name(),
                    )
                    NotificationLog.objects.create(
                        entity_type="expense",
                        entity_id=expense.id,
                        notification_type="approval_reminder",
                        channel="email",
                        recipient=expense.approver.email,
                        status="sent",
                    )
                    count += 1
                    logger.info(
                        f"Sent expense approval reminder for expense #{expense.id}"
                    )
            except Exception as e:
                logger.error(f"Error sending expense notification: {str(e)}")

        logger.info(f"send_expense_notifications: Sent {count} notifications")
        return {"sent": count, "status": "success"}
    except Exception as e:
        logger.error(f"Error in send_expense_notifications: {str(e)}")
        return {"sent": 0, "status": "error"}
