"""
Signals for quotations app.
Auto-calculates totals when line items change.
Invalidates PDF cache when quote content changes.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Sum
from django.core.files.storage import default_storage
from decimal import Decimal
import logging
from .models import QuoteLineItem, Quote

logger = logging.getLogger(__name__)

# Content-affecting fields for Quote
QUOTE_CONTENT_FIELDS = {
    "status",
    "quote_date",
    "valid_until",
    "description",
    "currency",
    "subtotal_amount",
    "vat_amount",
    "total_amount",
}


@receiver(post_save, sender=QuoteLineItem)
@receiver(post_delete, sender=QuoteLineItem)
def update_quote_totals(sender, instance, **kwargs):
    """
    Recalculate quote totals whenever line items are added/removed/modified.
    Uses QuoteLineItem field names (line_amount, tax_amount, line_total).
    Clears cached PDF since content has changed.
    """
    quote = instance.quote
    line_items = quote.line_items.all()

    # Calculate totals using QuoteLineItem fields
    # NOTE: QuoteLineItem uses line_amount (not line_subtotal like InvoiceLineItem)
    totals = line_items.aggregate(
        subtotal=Sum("line_amount"),
        vat=Sum("tax_amount"),
    )

    subtotal_amount = Decimal(str(totals["subtotal"] or "0.00"))
    vat_amount = Decimal(str(totals["vat"] or "0.00"))
    total_amount = subtotal_amount + vat_amount

    # Clear cached PDF since line items changed
    if quote.quote_pdf:
        try:
            if default_storage.exists(quote.quote_pdf.name):
                default_storage.delete(quote.quote_pdf.name)
            logger.info(
                f"Cleared cached PDF for quotation {quote.quote_number} due to line item change"
            )
        except Exception as e:
            logger.warning(f"Could not delete cached PDF: {str(e)}")

    quote.subtotal_amount = subtotal_amount
    quote.vat_amount = vat_amount
    quote.total_amount = total_amount
    quote.quote_pdf = None  # Clear PDF field
    quote.save(
        update_fields=[
            "subtotal_amount",
            "vat_amount",
            "total_amount",
            "quote_pdf",
            "updated_at",
        ]
    )

    # Auto-expire quotes past valid_until date
    if quote.status not in ["converted", "accepted", "rejected", "expired"]:
        if timezone.now().date() > quote.valid_until:
            quote.status = "expired"
            quote.expired_at = timezone.now()
            quote.save(update_fields=["status", "expired_at"])


@receiver(post_save, sender=Quote)
def invalidate_quote_pdf_on_content_change(
    sender, instance, created, update_fields, **kwargs
):
    """
    Clear cached PDF when quote content changes.
    Does NOT clear PDF for metadata-only changes (sent_at, viewed_at, etc).
    """
    # Skip if this is a newly created quote or if it's a save operation we triggered
    if created:
        return

    # Determine which fields were updated
    # If update_fields is None, all fields were updated
    if update_fields is None:
        # Full save - clear cache
        content_changed = True
    else:
        # Partial save - check if content fields changed
        content_changed = bool(QUOTE_CONTENT_FIELDS & set(update_fields))

    if content_changed and instance.quote_pdf:
        try:
            # Delete cached PDF file
            if default_storage.exists(instance.quote_pdf.name):
                default_storage.delete(instance.quote_pdf.name)
            logger.info(
                f"Cleared cached PDF for quotation {instance.quote_number} due to content change"
            )

            # Clear PDF field without triggering this signal again
            Quote.objects.filter(id=instance.id).update(quote_pdf=None)
        except Exception as e:
            logger.warning(f"Could not delete cached PDF: {str(e)}")
