"""
Email sending service for the invoicing application.

Handles email delivery with template support and async processing via Celery.
Supports:
- Invoice delivery (PDF attachment)
- Payment confirmations
- Reminders (overdue, due soon)
- Notifications
"""

from typing import Dict, List, Optional
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending templated emails."""

    def __init__(self):
        self.sender = settings.DEFAULT_FROM_EMAIL
        self.sender_name = "Invoice Management"

    def send_invoice_issued_notification(
        self,
        client_email: str,
        client_name: str,
        invoice_number: str,
        invoice_date: str,
        total_amount: str,
        due_date: str,
        pdf_content: Optional[bytes] = None,
    ) -> bool:
        """
        Send invoice to client when issued.

        Args:
            client_email: Recipient email address
            client_name: Client/customer name
            invoice_number: Invoice number (e.g., "INV-2026-0001")
            invoice_date: Date invoice was issued
            total_amount: Invoice total with currency
            due_date: Payment due date
            pdf_content: Optional invoice PDF bytes

        Returns:
            True if sent successfully, False otherwise
        """
        context = {
            'client_name': client_name,
            'invoice_number': invoice_number,
            'invoice_date': invoice_date,
            'total_amount': total_amount,
            'due_date': due_date,
        }

        subject = f"Invoice {invoice_number} - {self.sender_name}"
        html_message = render_to_string(
            'emails/invoice_issued.html',
            context
        )
        text_message = strip_tags(html_message)

        return self._send_email(
            subject=subject,
            html_message=html_message,
            text_message=text_message,
            recipient_email=client_email,
            pdf_attachment=pdf_content,
            pdf_filename=f"{invoice_number}.pdf" if pdf_content else None,
        )

    def send_quote_issued_notification(
        self,
        client_email: str,
        client_name: str,
        quote_number: str,
        quote_date: str,
        total_amount: str,
        valid_until: str,
        pdf_content: Optional[bytes] = None,
    ) -> bool:
        """
        Send quotation to client when issued.

        Args:
            client_email: Recipient email address
            client_name: Client/customer name
            quote_number: Quote number (e.g., "QUOTE-2026-0001")
            quote_date: Date quote was created
            total_amount: Quote total with currency
            valid_until: Quote expiration date
            pdf_content: Optional quote PDF bytes

        Returns:
            True if sent successfully, False otherwise
        """
        context = {
            'client_name': client_name,
            'quote_number': quote_number,
            'quote_date': quote_date,
            'total_amount': total_amount,
            'valid_until': valid_until,
        }

        subject = f"Quotation {quote_number} - {self.sender_name}"
        html_message = render_to_string(
            'emails/quote_issued.html',
            context
        )
        text_message = strip_tags(html_message)

        return self._send_email(
            subject=subject,
            html_message=html_message,
            text_message=text_message,
            recipient_email=client_email,
            pdf_attachment=pdf_content,
            pdf_filename=f"{quote_number}.pdf" if pdf_content else None,
        )

    def send_payment_confirmation(
        self,
        client_email: str,
        client_name: str,
        invoice_number: str,
        payment_amount: str,
        payment_date: str,
        payment_method: str,
    ) -> bool:
        """Send payment confirmation to client."""
        context = {
            'client_name': client_name,
            'invoice_number': invoice_number,
            'payment_amount': payment_amount,
            'payment_date': payment_date,
            'payment_method': payment_method,
        }

        subject = f"Payment Confirmed - Invoice {invoice_number}"
        html_message = render_to_string(
            'emails/payment_confirmation.html',
            context
        )
        text_message = strip_tags(html_message)

        return self._send_email(
            subject=subject,
            html_message=html_message,
            text_message=text_message,
            recipient_email=client_email,
        )

    def send_overdue_reminder(
        self,
        client_email: str,
        client_name: str,
        invoice_number: str,
        amount_due: str,
        original_due_date: str,
        days_overdue: int,
    ) -> bool:
        """Send overdue payment reminder."""
        context = {
            'client_name': client_name,
            'invoice_number': invoice_number,
            'amount_due': amount_due,
            'original_due_date': original_due_date,
            'days_overdue': days_overdue,
        }

        subject = f"URGENT: Invoice {invoice_number} is {days_overdue} days overdue"
        html_message = render_to_string(
            'emails/overdue_reminder.html',
            context
        )
        text_message = strip_tags(html_message)

        return self._send_email(
            subject=subject,
            html_message=html_message,
            text_message=text_message,
            recipient_email=client_email,
        )

    def send_due_soon_reminder(
        self,
        client_email: str,
        client_name: str,
        invoice_number: str,
        amount_due: str,
        due_date: str,
        days_until_due: int,
    ) -> bool:
        """Send reminder for invoice due soon."""
        context = {
            'client_name': client_name,
            'invoice_number': invoice_number,
            'amount_due': amount_due,
            'due_date': due_date,
            'days_until_due': days_until_due,
        }

        subject = f"Reminder: Invoice {invoice_number} due in {days_until_due} days"
        html_message = render_to_string(
            'emails/due_soon_reminder.html',
            context
        )
        text_message = strip_tags(html_message)

        return self._send_email(
            subject=subject,
            html_message=html_message,
            text_message=text_message,
            recipient_email=client_email,
        )

    def send_bulk_email(
        self,
        subject: str,
        html_message: str,
        recipient_emails: List[str],
    ) -> Dict[str, bool]:
        """
        Send same email to multiple recipients.

        Args:
            subject: Email subject
            html_message: HTML content
            recipient_emails: List of recipient email addresses

        Returns:
            Dictionary mapping email -> success (True/False)
        """
        results = {}
        text_message = strip_tags(html_message)

        for email in recipient_emails:
            results[email] = self._send_email(
                subject=subject,
                html_message=html_message,
                text_message=text_message,
                recipient_email=email,
            )

        return results

    def _send_email(
        self,
        subject: str,
        html_message: str,
        text_message: str,
        recipient_email: str,
        pdf_attachment: Optional[bytes] = None,
        pdf_filename: Optional[str] = None,
    ) -> bool:
        """
        Internal method to actually send the email.

        Args:
            subject: Email subject
            html_message: HTML message body
            text_message: Plain text message body (fallback)
            recipient_email: Recipient email address
            pdf_attachment: Optional PDF bytes to attach
            pdf_filename: Filename for PDF attachment

        Returns:
            True if successful, False otherwise
        """
        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=self.sender,
                to=[recipient_email],
            )
            email.attach_alternative(html_message, "text/html")

            if pdf_attachment and pdf_filename:
                email.attach(pdf_filename, pdf_attachment, "application/pdf")

            email.send(fail_silently=False)
            logger.info(f"Email sent successfully to {recipient_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            return False


# Singleton instance
email_service = EmailService()
