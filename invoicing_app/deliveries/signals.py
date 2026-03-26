"""Signals for deliveries app."""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from invoicing_app.deliveries.models import Delivery, DeliveryNumberSequence


@receiver(post_save, sender=Delivery)
def auto_generate_delivery_number(sender, instance, created, **kwargs):
    """Auto-generate delivery number and tracking number if not already set."""
    needs_save = False
    
    if created and not instance.delivery_number:
        # Get settings
        from invoicing_app.core.models import CompanySettings
        settings = CompanySettings.get_settings()
        prefix = settings.delivery_prefix
        
        # Get current year
        year = timezone.now().year
        
        # Get or create sequence
        sequence, _ = DeliveryNumberSequence.objects.get_or_create(
            prefix=prefix,
            year=year
        )
        
        # Generate number atomically
        from django.db import transaction
        with transaction.atomic():
            sequence = DeliveryNumberSequence.objects.select_for_update().get(
                prefix=prefix,
                year=year
            )
            number = sequence.next_sequence
            sequence.next_sequence += 1
            sequence.save(update_fields=['next_sequence'])
        
        # Update delivery with number
        instance.delivery_number = f"{prefix}-{year}-{number:04d}"
        needs_save = True
    
    # Generate tracking number if not already set
    if created and not instance.tracking_number:
        """
        Generate tracking number with format: PREFIX-TRK-YEAR-ID
        Example: OG-TRK-2026-00001 (where 00001 is the delivery ID)
        This makes it easy to trace back to delivery records
        """
        year = timezone.now().year
        # Extract prefix from delivery number or settings
        from invoicing_app.core.models import CompanySettings
        settings = CompanySettings.get_settings()
        prefix = settings.delivery_prefix
        
        # Format tracking number with padded instance ID: PREFIX-TRK-YEAR-ID
        instance.tracking_number = f"{prefix}-TRK-{year}-{instance.id:05d}"
        needs_save = True
    
    if needs_save:
        instance.save(update_fields=['delivery_number', 'tracking_number'])
