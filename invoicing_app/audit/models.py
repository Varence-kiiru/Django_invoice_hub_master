"""
Audit and compliance models.
Immutable snapshots and event logs for KRA compliance.
"""
from django.db import models
from django.utils import timezone


class InvoiceSnapshot(models.Model):
    """
    Immutable copy of invoice state for KRA eTIMS compliance.
    Read-only after creation; stores full JSON dump of invoice.
    """
    id = models.BigAutoField(primary_key=True)
    invoice = models.OneToOneField(
        'invoices.Invoice',
        on_delete=models.PROTECT,
        related_name='snapshot',
        help_text="Invoice this snapshot is for"
    )
    invoice_number = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Denormalized invoice number for quick lookup"
    )
    snapshot_date = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When this snapshot was taken"
    )
    snapshot_version = models.IntegerField(
        default=1,
        help_text="Version number (for edited invoices)"
    )
    invoice_state_json = models.JSONField(
        help_text="Full JSON dump of invoice at snapshot time"
    )
    kra_etims_receipt = models.TextField(
        blank=True,
        null=True,
        help_text="KRA eTIMS receipt/confirmation (future)"
    )
    is_kra_verified = models.BooleanField(
        default=False,
        help_text="Has KRA acknowledged this invoice?"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_invoicesnapshot'
        ordering = ['-snapshot_date']
        indexes = [
            models.Index(fields=['invoice']),
            models.Index(fields=['invoice_number']),
            models.Index(fields=['snapshot_date']),
        ]

    def __str__(self):
        return f"Snapshot {self.invoice_number} v{self.snapshot_version}"

    def save(self, *args, **kwargs):
        """Prevent updates to existing snapshots (immutable)."""
        if self.pk is not None:
            raise ValueError("InvoiceSnapshot is immutable; cannot update after creation")
        super().save(*args, **kwargs)


class AuditLog(models.Model):
    """
    Immutable event log for all entity changes.
    Insert-only, no updates. One entry per change.
    """
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
        ('issued', 'Issued'),
        ('sent', 'Sent to Client'),
        ('viewed', 'Viewed by Client'),
        ('paid', 'Marked as Paid'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.BigAutoField(primary_key=True)
    entity_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Entity type (invoice, payment, client, etc.)"
    )
    entity_id = models.BigIntegerField(
        help_text="ID of entity modified"
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        db_index=True,
        help_text="Action taken"
    )
    old_values = models.JSONField(
        blank=True,
        null=True,
        help_text="Previous values (for updates)"
    )
    new_values = models.JSONField(
        blank=True,
        null=True,
        help_text="New values (for updates)"
    )
    actor = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_events',
        help_text="User who made the change"
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When change occurred"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of request (for security audit)"
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Browser/app user agent"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional context"
    )
    is_kra_verified = models.BooleanField(
        default=False,
        help_text="Has KRA acknowledged this change?"
    )

    class Meta:
        db_table = 'audit_auditlog'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['actor']),
        ]

    def __str__(self):
        return f"{self.entity_type}:{self.entity_id} - {self.action} by {self.actor}"

    def save(self, *args, **kwargs):
        """Prevent updates (insert-only log)."""
        if self.pk is not None:
            raise ValueError("AuditLog is immutable; cannot update after creation")
        super().save(*args, **kwargs)


class LoginHistory(models.Model):
    """
    Keep track of user login attempts and sessions.
    Used for security auditing and account activity monitoring.
    """
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='login_history',
        help_text="User who logged in"
    )
    login_time = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When user logged in"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of login"
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Browser/device information"
    )
    device_info = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Extracted device name (Chrome, Safari, etc.)"
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Geographic location (from IP lookup)"
    )
    session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Django session ID"
    )
    logout_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user logged out"
    )
    is_successful = models.BooleanField(
        default=True,
        help_text="Whether login was successful"
    )

    class Meta:
        db_table = 'audit_loginhistory'
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['user', '-login_time']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['login_time']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.login_time.strftime('%Y-%m-%d %H:%M:%S')}"

    def get_device_display(self):
        """Return a human-readable device name from user agent."""
        if self.device_info:
            return self.device_info
        
        ua = self.user_agent or ""
        if "Chrome" in ua:
            return "Chrome on Windows"
        elif "Firefox" in ua:
            return "Firefox"
        elif "Safari" in ua:
            return "Safari on macOS" if "Mac" in ua else "Safari"
        elif "Mobile" in ua:
            return "Mobile"
        else:
            return "Unknown Device"
    def set_location_from_ip(self):
        """Fetch and set location from IP address using ipapi.co API."""
        if not self.ip_address or self.location:
            return  # Skip if no IP or location already set
        
        # Skip private/local IPs
        if self.ip_address.startswith(('127.', '192.168.', '10.', '172.')):
            self.location = "Local/Private Network"
            return
        
        try:
            import requests
            # Use ipapi.co which is free and fast
            response = requests.get(
                f'https://ipapi.co/{self.ip_address}/json/',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                city = data.get('city', '')
                region = data.get('region', '')
                country = data.get('country_name', '')
                
                # Build location string
                location_parts = [p for p in [city, region, country] if p]
                if location_parts:
                    self.location = ', '.join(location_parts)
                else:
                    self.location = f"{country}" if country else "Unknown"
            else:
                self.location = "Lookup failed"
        except Exception as e:
            # Silently fail if API is unavailable
            self.location = "Location unavailable"