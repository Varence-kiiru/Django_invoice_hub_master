"""
Notifications models (placeholder for future functionality).
"""
from django.db import models


class EmailTemplate(models.Model):
    """
    Email templates for invoicing notifications.
    """
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Template name (invoice_issued, payment_reminder, etc.)"
    )
    subject = models.CharField(
        max_length=200,
        help_text="Email subject template"
    )
    body = models.TextField(
        help_text="Email body template (supports Django template syntax)"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this template is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notifications_emailtemplate'
        ordering = ['name']

    def __str__(self):
        return self.name


class NotificationLog(models.Model):
    """
    Log of all notifications sent (email, SMS, etc.).
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    id = models.BigAutoField(primary_key=True)
    entity_type = models.CharField(
        max_length=50,
        help_text="Entity type (invoice, payment, etc.)"
    )
    entity_id = models.BigIntegerField(
        help_text="ID of entity"
    )
    notification_type = models.CharField(
        max_length=50,
        help_text="Type of notification (email_sent, payment_reminder, etc.)"
    )
    recipient = models.CharField(
        max_length=255,
        help_text="Recipient email or phone"
    )
    subject = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Email subject or SMS content"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Notification status"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if failed"
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notification was sent"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications_notificationlog'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.notification_type} to {self.recipient} ({self.get_status_display()})"
