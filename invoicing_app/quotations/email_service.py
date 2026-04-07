"""
Email notification service for Quotations.
Handles sending quotations to clients and status change notifications.
"""

from typing import Optional
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class QuoteEmailService:
    """Service for sending quotation emails."""

    def __init__(self):
        self.sender = settings.DEFAULT_FROM_EMAIL
        self.sender_name = "Quote Management"

    def send_quote_issued(
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
        Send quotation to client.

        Args:
            client_email: Recipient email address
            client_name: Client/customer name
            quote_number: Quotation number (e.g., "QUOTE-2026-0001")
            quote_date: Date quotation was issued
            total_amount: Quotation total with currency
            valid_until: Quotation validity date
            pdf_content: Optional quotation PDF bytes

        Returns:
            True if sent successfully, False otherwise
        """
        context = {
            "client_name": client_name,
            "quote_number": quote_number,
            "quote_date": quote_date,
            "total_amount": total_amount,
            "valid_until": valid_until,
        }

        subject = f"Quotation {quote_number} - {self.sender_name}"
        html_message = render_to_string("emails/quote_issued.html", context)
        text_message = strip_tags(html_message)

        return self._send_email(
            subject=subject,
            html_message=html_message,
            text_message=text_message,
            recipient_email=client_email,
            pdf_attachment=pdf_content,
            pdf_filename=f"{quote_number}.pdf" if pdf_content else None,
        )

    def send_quote_accepted(
        self,
        client_email: str,
        client_name: str,
        quote_number: str,
        total_amount: str,
    ) -> bool:
        """Send notification when client accepts quotation."""
        context = {
            "client_name": client_name,
            "quote_number": quote_number,
            "total_amount": total_amount,
        }

        subject = f"Quotation Accepted - {quote_number}"
        html_message = render_to_string("emails/quote_accepted.html", context)
        text_message = strip_tags(html_message)

        return self._send_email(
            subject=subject,
            html_message=html_message,
            text_message=text_message,
            recipient_email=client_email,
        )

    def send_quote_rejected(
        self,
        client_email: str,
        client_name: str,
        quote_number: str,
        rejection_reason: str = None,
    ) -> bool:
        """Send notification when client rejects quotation."""
        context = {
            "client_name": client_name,
            "quote_number": quote_number,
            "rejection_reason": rejection_reason or "No reason provided",
        }

        subject = f"Quotation Rejected - {quote_number}"
        html_message = render_to_string("emails/quote_rejected.html", context)
        text_message = strip_tags(html_message)

        return self._send_email(
            subject=subject,
            html_message=html_message,
            text_message=text_message,
            recipient_email=client_email,
        )

    def send_quote_expiration_warning(
        self,
        client_email: str,
        client_name: str,
        quote_number: str,
        valid_until: str,
        days_remaining: int,
    ) -> bool:
        """Send reminder before quotation expires."""
        context = {
            "client_name": client_name,
            "quote_number": quote_number,
            "valid_until": valid_until,
            "days_remaining": days_remaining,
        }

        subject = f"Quotation Expiring Soon - {quote_number}"
        html_message = render_to_string("emails/quote_expiration_warning.html", context)
        text_message = strip_tags(html_message)

        return self._send_email(
            subject=subject,
            html_message=html_message,
            text_message=text_message,
            recipient_email=client_email,
        )

    def send_quote_converted(
        self,
        client_email: str,
        client_name: str,
        quote_number: str,
        invoice_number: str,
        total_amount: str,
        due_date: str,
    ) -> bool:
        """Send notification when quotation is converted to invoice."""
        context = {
            "client_name": client_name,
            "quote_number": quote_number,
            "invoice_number": invoice_number,
            "total_amount": total_amount,
            "due_date": due_date,
        }

        subject = f"Invoice Generated from {quote_number}"
        html_message = render_to_string("emails/quote_converted.html", context)
        text_message = strip_tags(html_message)

        return self._send_email(
            subject=subject,
            html_message=html_message,
            text_message=text_message,
            recipient_email=client_email,
        )

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
        Internal method to send email with optional PDF attachment.

        Args:
            subject: Email subject
            html_message: HTML email body
            text_message: Plain text email body
            recipient_email: Recipient email address
            pdf_attachment: Optional PDF file bytes
            pdf_filename: Optional filename for PDF attachment

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if pdf_attachment:
                # Use EmailMultiAlternatives for HTML + plain text + attachment
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_message,
                    from_email=self.sender,
                    to=[recipient_email],
                )
                email.attach_alternative(html_message, "text/html")
                email.attach(
                    pdf_filename or "document.pdf", pdf_attachment, "application/pdf"
                )
            else:
                # Use EmailMultiAlternatives for HTML + plain text
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_message,
                    from_email=self.sender,
                    to=[recipient_email],
                )
                email.attach_alternative(html_message, "text/html")

            email.send()
            logger.info(f"Email sent successfully to {recipient_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            return False
