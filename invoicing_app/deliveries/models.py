"""
Delivery models for tracking goods/services delivery to customers.
"""
from django.db import models
from django.utils import timezone
from invoicing_app.core.models import ActiveModel, generate_uuid


class DeliveryNumberSequence(models.Model):
    """
    Generates unique, non-gapped delivery numbers per prefix/year.
    Uses SELECT FOR UPDATE for concurrent-safe incrementing.
    """
    id = models.BigAutoField(primary_key=True)
    prefix = models.CharField(
        max_length=20,
        default='DLV',
        help_text="Delivery number prefix (DLV, CHALLAN, etc.)"
    )
    year = models.IntegerField(
        help_text="Calendar year"
    )
    next_sequence = models.BigIntegerField(
        default=1,
        help_text="Next sequence number to use"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'deliveries_deliverynumbersequence'
        unique_together = [['prefix', 'year']]
        indexes = [
            models.Index(fields=['prefix', 'year']),
        ]

    def __str__(self):
        return f"{self.prefix}-{self.year}: next={self.next_sequence}"


class Delivery(ActiveModel):
    """
    Delivery record with status tracking and proof of delivery.
    Links to a single invoice and tracks partial/full deliveries.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('partially_delivered', 'Partially Delivered'),
        ('failed', 'Delivery Failed'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
    ]

    # ━━━ Override inherited uuid to not be unique (delivery_number is our unique identifier) ━━━
    uuid = models.CharField(
        max_length=36,
        db_index=True,
        default=generate_uuid,
        editable=False,
        help_text="External API reference (UUID4)"
    )

    # ━━━ Identity ━━━
    delivery_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Delivery challan number (e.g., DLV-2026-0001)"
    )

    # ━━━ References ━━━
    invoice = models.ForeignKey(
        'invoices.Invoice',
        on_delete=models.PROTECT,
        related_name='deliveries',
        help_text="Invoice this delivery is for"
    )

    # ━━━ Dates & Times ━━━
    scheduled_date = models.DateField(
        default=timezone.now,
        db_index=True,
        help_text="Scheduled delivery date"
    )
    actual_delivery_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Actual delivery date"
    )
    delivery_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Time of delivery"
    )

    # ━━━ Status & Tracking ━━━
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True,
        help_text="Delivery status"
    )
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text="Courier/tracking number"
    )

    # ━━━ Delivery Details ━━━
    delivery_method = models.CharField(
        max_length=50,
        choices=[
            ('hand_delivery', 'Hand Delivery'),
            ('courier', 'Courier Service'),
            ('pickup', 'Customer Pickup'),
            ('email', 'Email/Digital'),
            ('other', 'Other'),
        ],
        default='hand_delivery',
        help_text="How items are delivered"
    )
    delivery_location = models.TextField(
        blank=True,
        null=True,
        help_text="Delivery address/location"
    )
    recipient_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Name of person receiving delivery"
    )
    recipient_signature_url = models.FileField(
        upload_to='deliveries/signatures/',
        null=True,
        blank=True,
        help_text="Digital signature proof of delivery"
    )

    # ━━━ Condition & Quality ━━━
    condition = models.CharField(
        max_length=50,
        choices=[
            ('good', 'Good Condition'),
            ('damaged', 'Damaged'),
            ('partial', 'Partial/Incomplete'),
            ('not_delivered', 'Not Deliverable'),
        ],
        default='good',
        help_text="Condition of items upon delivery"
    )
    condition_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Details about item condition or issues"
    )

    # ━━━ General ━━━
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional delivery notes"
    )
    delivery_pdf = models.FileField(
        upload_to='deliveries/pdfs/',
        null=True,
        blank=True,
        help_text="Generated PDF delivery challan"
    )

    # ━━━ Metadata ━━━
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_deliveries',
        help_text="User who created this delivery"
    )
    # Note: created_at and updated_at inherited from BaseModel via ActiveModel

    class Meta:
        db_table = 'deliveries_delivery'
        ordering = ['-delivery_number']
        indexes = [
            models.Index(fields=['invoice', 'status']),
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['actual_delivery_date']),
        ]

    def __str__(self):
        return f"{self.delivery_number} - {self.invoice.invoice_number}"

    @property
    def total_items_scheduled(self):
        """Calculate total items scheduled for delivery."""
        return self.line_items.aggregate(
            total=models.Sum('quantity_scheduled')
        )['total'] or 0

    @property
    def total_items_delivered(self):
        """Calculate total items actually delivered."""
        return self.line_items.aggregate(
            total=models.Sum('quantity_delivered')
        )['total'] or 0

    @property
    def is_fully_delivered(self):
        """Check if all items have been delivered."""
        if not self.line_items.exists():
            return False
        return all(
            item.quantity_delivered >= item.quantity_scheduled 
            for item in self.line_items.all()
        )

    @property
    def is_partially_delivered(self):
        """Check if some items have been delivered."""
        if not self.line_items.exists():
            return False
        delivered_count = sum(
            1 for item in self.line_items.all()
            if item.quantity_delivered > 0
        )
        return 0 < delivered_count < self.line_items.count()


class DeliveryLineItem(models.Model):
    """
    Individual line items in a delivery.
    Tracks quantity scheduled vs. quantity delivered for each product.
    """
    id = models.BigAutoField(primary_key=True)
    delivery = models.ForeignKey(
        Delivery,
        on_delete=models.CASCADE,
        related_name='line_items',
        help_text="Parent delivery"
    )
    invoice_line = models.ForeignKey(
        'invoices.InvoiceLineItem',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='delivery_items',
        help_text="Related invoice line item"
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='deliveries',
        help_text="Product being delivered"
    )

    # ━━━ Quantities ━━━
    quantity_scheduled = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Quantity scheduled for delivery"
    )
    quantity_delivered = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Quantity actually delivered"
    )
    unit = models.CharField(
        max_length=20,
        default='pcs',
        help_text="Unit of measurement (pcs, kg, liters, etc.)"
    )

    # ━━━ Details ━━━
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Item description"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Any notes about this item"
    )

    # ━━━ Metadata ━━━
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'deliveries_deliverylineitem'
        ordering = ['id']

    def __str__(self):
        return f"{self.product.name} x {self.quantity_scheduled} {self.unit}"

    @property
    def shortfall(self):
        """Calculate quantity not yet delivered."""
        return max(0, self.quantity_scheduled - self.quantity_delivered)

    @property
    def is_fully_delivered(self):
        """Check if item has been fully delivered."""
        return self.quantity_delivered >= self.quantity_scheduled
