"""
Core shared models, base classes, and utilities.
"""
import uuid
from datetime import datetime
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from cryptography.fernet import Fernet, InvalidToken
import logging

logger = logging.getLogger(__name__)


def generate_uuid():
    """Generate a string UUID for model defaults."""
    return str(uuid.uuid4())


class BaseModel(models.Model):
    """
    Abstract base model with common fields for all entities.
    Provides: id, uuid, created_at, updated_at, is_active.
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.CharField(
        max_length=36,
        unique=True,
        db_index=True,
        default=generate_uuid,
        editable=False,
        help_text="External API reference (UUID4)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this record was last updated"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Soft delete flag"
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']


class TimeStampedModel(models.Model):
    """
    Abstract base model with only timestamps (no UUID or is_active).
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this record was last updated"
    )

    class Meta:
        abstract = True


class IsActiveManager(models.Manager):
    """
    Manager that filters only active records by default.
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class ActiveModel(BaseModel):
    """
    Convenience model that includes IsActiveManager by default.
    """
    objects = IsActiveManager()
    all_objects = models.Manager()  # To get all records including inactive

    class Meta:
        abstract = True


class Backup(TimeStampedModel):
    """
    Database backup tracking model.
    Records information about database backups for restore operations.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
        ('failed', 'Failed'),
        ('verified', 'Verified'),
    ]
    
    BACKUP_TYPE_CHOICES = [
        ('database', 'Database'),
        ('full', 'Full System'),
        ('incremental', 'Incremental'),
    ]
    
    file_name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Name of backup file"
    )
    file_path = models.CharField(
        max_length=500,
        help_text="Full path to backup file on disk"
    )
    file_size = models.BigIntegerField(
        help_text="Size of backup in bytes"
    )
    backup_type = models.CharField(
        max_length=20,
        choices=BACKUP_TYPE_CHOICES,
        default='database',
        help_text="Type of backup"
    )
    duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="How long backup took to complete"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Current backup status"
    )
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='backup_created',
        help_text="User who initiated backup"
    )
    checksum = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="SHA256 checksum for integrity verification"
    )
    is_compressed = models.BooleanField(
        default=False,
        help_text="Whether backup is compressed"
    )
    is_automated = models.BooleanField(
        default=False,
        help_text="Was this backup created automatically?"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional backup notes"
    )
    restored_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this backup was last restored"
    )
    restored_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='backup_restored',
        help_text="User who restored from this backup"
    )
    
    class Meta:
        db_table = 'core_backup'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['backup_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.file_name} ({self.get_status_display()})"
    
    def get_file_size_mb(self):
        """Return file size in MB."""
        return round(self.file_size / (1024 * 1024), 2)
    
    def get_duration_display(self):
        """Display duration in human-readable format."""
        if not self.duration_seconds:
            return "N/A"
        
        seconds = self.duration_seconds
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"


class CompanySettings(TimeStampedModel):
    """
    Singleton model for storing company-wide settings.
    Only one instance should exist - enforced via manager.
    
    Stores company branding, contact details, and configuration
    used across invoices, emails, and other documents.
    """
    id = models.BigAutoField(primary_key=True)
    
    # Company Identity
    company_name = models.CharField(
        max_length=255,
        default="Your Company Name",
        help_text="Official company name"
    )
    company_website = models.URLField(
        blank=True,
        null=True,
        help_text="Company website URL"
    )
    company_logo = models.ImageField(
        upload_to='company/',
        blank=True,
        null=True,
        help_text="Company logo image (PNG/JPG, max 2MB, recommended 300x150px)"
    )
    
    # Contact Details
    company_email = models.EmailField(
        default="info@yourcompany.com",
        help_text="Primary contact email address"
    )
    company_phone = models.CharField(
        max_length=20,
        default="+1-234-567-8900",
        help_text="Primary phone number"
    )
    company_address = models.TextField(
        default="123 Business St, City, Country",
        help_text="Full company address"
    )
    
    # Tax Information
    tax_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Tax ID / VAT Registration Number (e.g., KRA PIN for Kenya)"
    )
    
    # Invoice Settings
    invoice_prefix = models.CharField(
        max_length=10,
        default="INV",
        help_text="Prefix for invoice numbers (e.g., INV-2026-0001)"
    )
    payment_prefix = models.CharField(
        max_length=10,
        default="REC",
        help_text="Prefix for payment receipt numbers (e.g., REC-2026-0001)"
    )
    quote_prefix = models.CharField(
        max_length=10,
        default="QUOTE",
        help_text="Prefix for quotation numbers (e.g., QUOTE-2026-0001)"
    )
    financial_year_start = models.IntegerField(
        default=1,
        help_text="Month number when financial year starts (1-12)"
    )
    
    # Payment Terms
    default_payment_terms = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Default payment terms for invoices (e.g., Net 30 days)"
    )
    
    # Bank Details
    bank_account_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Bank account holder name"
    )
    bank_account_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Bank account number"
    )
    bank_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Bank name"
    )
    bank_branch = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Bank branch (optional)"
    )
    bank_swift_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="SWIFT code (optional, for international transfers)"
    )
    bank_iban = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="IBAN (optional, for international transfers)"
    )
    
    # M-Pesa Details
    mpesa_paybill_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="M-Pesa Paybill number (e.g., 123456)"
    )
    mpesa_account_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="M-Pesa account name / reference (what customer enters as reference)"
    )
    mpesa_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="M-Pesa till number or phone (optional, for alternative payment method)"
    )
    
    # System Preferences
    TIMEZONE_CHOICES = [
        ('America/New_York', 'America/New_York'),
        ('America/Chicago', 'America/Chicago'),
        ('America/Los_Angeles', 'America/Los_Angeles'),
        ('America/Denver', 'America/Denver'),
        ('America/Anchorage', 'America/Anchorage'),
        ('America/Toronto', 'America/Toronto'),
        ('America/Mexico_City', 'America/Mexico_City'),
        ('America/Sao_Paulo', 'America/Sao_Paulo'),
        ('America/Buenos_Aires', 'America/Buenos_Aires'),
        ('Europe/London', 'Europe/London'),
        ('Europe/Paris', 'Europe/Paris'),
        ('Europe/Berlin', 'Europe/Berlin'),
        ('Europe/Amsterdam', 'Europe/Amsterdam'),
        ('Europe/Rome', 'Europe/Rome'),
        ('Europe/Stockholm', 'Europe/Stockholm'),
        ('Europe/Moscow', 'Europe/Moscow'),
        ('Africa/Cairo', 'Africa/Cairo'),
        ('Africa/Johannesburg', 'Africa/Johannesburg'),
        ('Africa/Lagos', 'Africa/Lagos'),
        ('Africa/Nairobi', 'Africa/Nairobi'),
        ('Asia/Dubai', 'Asia/Dubai'),
        ('Asia/Kolkata', 'Asia/Kolkata'),
        ('Asia/Bangkok', 'Asia/Bangkok'),
        ('Asia/Hong_Kong', 'Asia/Hong_Kong'),
        ('Asia/Tokyo', 'Asia/Tokyo'),
        ('Asia/Seoul', 'Asia/Seoul'),
        ('Australia/Sydney', 'Australia/Sydney'),
        ('Australia/Melbourne', 'Australia/Melbourne'),
        ('Pacific/Auckland', 'Pacific/Auckland'),
        ('UTC', 'UTC'),
    ]
    
    timezone = models.CharField(
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default='UTC',
        help_text="System timezone for date/time operations"
    )
    
    DATE_FORMAT_CHOICES = [
        ('MM/DD/YYYY', 'MM/DD/YYYY (12-31-2026)'),
        ('DD/MM/YYYY', 'DD/MM/YYYY (31-12-2026)'),
        ('YYYY-MM-DD', 'YYYY-MM-DD (2026-12-31)'),
    ]
    
    date_format = models.CharField(
        max_length=20,
        choices=DATE_FORMAT_CHOICES,
        default='MM/DD/YYYY',
        help_text="Display format for dates throughout the system"
    )
    
    currency_symbol = models.CharField(
        max_length=10,
        default='$',
        help_text="Default currency symbol or code to display"
    )
    
    CURRENCY_CHOICES = [
        ('KES', 'Kenyan Shilling (KES)'),
        ('USD', 'US Dollar (USD)'),
        ('EUR', 'Euro (EUR)'),
        ('GBP', 'British Pound (GBP)'),
        ('JPY', 'Japanese Yen (JPY)'),
        ('AUD', 'Australian Dollar (AUD)'),
        ('CAD', 'Canadian Dollar (CAD)'),
        ('CHF', 'Swiss Franc (CHF)'),
        ('CNY', 'Chinese Yuan (CNY)'),
        ('INR', 'Indian Rupee (INR)'),
        ('ZAR', 'South African Rand (ZAR)'),
        ('NGN', 'Nigerian Naira (NGN)'),
    ]
    
    default_currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='KES',
        help_text="Default currency code for all transactions"
    )
    
    DECIMAL_CHOICES = [
        ('2', '2 decimal places (1,234.56)'),
        ('3', '3 decimal places (1,234.567)'),
        ('4', '4 decimal places (1,234.5678)'),
    ]
    
    decimal_places = models.CharField(
        max_length=1,
        choices=DECIMAL_CHOICES,
        default='2',
        help_text="Number of decimal places for currency display"
    )
    
    # Terms and Conditions
    terms_and_conditions = models.TextField(
        blank=True,
        null=True,
        help_text="Default terms and conditions to display on quotations and invoices"
    )
    
    # Feature Toggles
    enable_payments = models.BooleanField(
        default=True,
        help_text="Enable payment tracking and recording features"
    )
    enable_reminders = models.BooleanField(
        default=True,
        help_text="Enable automatic payment reminders for unpaid invoices"
    )
    enable_export = models.BooleanField(
        default=True,
        help_text="Enable export features (PDF, Excel, Reports)"
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_company_settings'
        verbose_name_plural = "Company Settings"
    
    def __str__(self):
        return f"Company Settings - {self.company_name}"
    
    @classmethod
    def get_settings(cls):
        """
        Get or create the singleton settings instance.
        
        Returns:
            CompanySettings instance
        """
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
    
    def save(self, *args, **kwargs):
        """Enforce singleton by always using pk=1."""
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion - settings should always exist."""
        raise ValueError("Cannot delete Company Settings. Reset values instead.")
    
    def get_logo_url(self):
        """Get URL to company logo image."""
        if self.company_logo:
            return self.company_logo.url
        return None
    
    # Feature Toggle Helpers
    def is_feature_enabled(self, feature_name):
        """
        Check if a specific feature is enabled.
        
        Args:
            feature_name: 'payments', 'reminders', or 'export'
        
        Returns:
            Boolean indicating if feature is enabled
        """
        features = {
            'payments': self.enable_payments,
            'reminders': self.enable_reminders,
            'export': self.enable_export,
        }
        return features.get(feature_name, False)


class EmailConfiguration(TimeStampedModel):
    """
    Singleton model for storing email configuration at runtime.
    Allows admin to configure SMTP settings through the UI without restarting Django.
    
    Only one instance should exist - enforced via manager.
    Passwords are encrypted using Fernet symmetric encryption.
    """
    id = models.BigAutoField(primary_key=True)
    
    # SMTP Configuration
    smtp_host = models.CharField(
        max_length=255,
        default='smtp.gmail.com',
        help_text="SMTP server hostname (e.g., smtp.gmail.com, smtp.office365.com)"
    )
    smtp_port = models.IntegerField(
        default=587,
        help_text="SMTP port number (typically 587 for TLS, 465 for SSL)"
    )
    smtp_username = models.CharField(
        max_length=255,
        default='',
        blank=True,
        help_text="SMTP authentication username (usually email address)"
    )
    smtp_password_encrypted = models.TextField(
        default='',
        blank=True,
        help_text="Encrypted SMTP password (write-only)"
    )
    smtp_use_tls = models.BooleanField(
        default=True,
        help_text="Use STARTTLS for SMTP connection"
    )
    smtp_use_ssl = models.BooleanField(
        default=False,
        help_text="Use SSL for SMTP connection (typically port 465)"
    )
    
    # Email Sender Information
    from_email = models.EmailField(
        default='no-reply@yourcompany.com',
        help_text="Email address to send from (verify this is authorized in your SMTP provider)"
    )
    from_name = models.CharField(
        max_length=255,
        default='Invoice System',
        help_text="Sender display name in email clients"
    )
    
    # Email Event Toggles
    enable_invoice_created = models.BooleanField(
        default=True,
        help_text="Send email when invoice is created"
    )
    enable_invoice_sent = models.BooleanField(
        default=True,
        help_text="Send email when invoice is marked as sent"
    )
    enable_payment_received = models.BooleanField(
        default=True,
        help_text="Send email when payment is received"
    )
    enable_payment_overdue = models.BooleanField(
        default=True,
        help_text="Send email for overdue payment reminders"
    )
    
    # Email Content Settings
    send_to_client_on_creation = models.BooleanField(
        default=False,
        help_text="Automatically send invoice to client when created"
    )
    days_before_due_reminder = models.IntegerField(
        default=3,
        help_text="Days before invoice is due to send reminder email"
    )
    
    # System Status Fields
    is_configured = models.BooleanField(
        default=False,
        help_text="Whether email configuration has been properly tested and is ready to use"
    )
    last_tested_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When SMTP connection was last tested"
    )
    last_test_status = models.CharField(
        max_length=50,
        choices=[
            ('pending', 'Pending Test'),
            ('success', 'Test Successful'),
            ('failed', 'Test Failed'),
            ('error', 'Configuration Error'),
        ],
        default='pending',
        help_text="Result of last SMTP test"
    )
    last_test_error = models.TextField(
        default='',
        blank=True,
        help_text="Error message from last failed test (for debugging)"
    )
    
    class Meta:
        db_table = 'core_email_configuration'
        verbose_name_plural = "Email Configuration"
    
    def __str__(self):
        return f"Email Configuration - {self.from_email}"
    
    @classmethod
    def get_config(cls):
        """
        Get or create the singleton email configuration instance.
        
        Returns:
            EmailConfiguration instance
        """
        config, created = cls.objects.get_or_create(pk=1)
        return config
    
    def save(self, *args, **kwargs):
        """Enforce singleton by always using pk=1."""
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion - config should always exist."""
        raise ValueError("Cannot delete Email Configuration. Reset values instead.")
    
    @staticmethod
    def _get_cipher():
        """
        Get or create Fernet cipher for encryption.
        Uses SECRET_KEY from Django settings.
        """
        from django.conf import settings
        from base64 import urlsafe_b64encode
        import hashlib
        
        # Create a consistent cipher from SECRET_KEY
        key = urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
        return Fernet(key)
    
    def _encrypt_password(self, password: str) -> str:
        """Encrypt password using Fernet."""
        if not password:
            return ''
        try:
            cipher = self._get_cipher()
            encrypted = cipher.encrypt(password.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Failed to encrypt email password: {e}")
            return ''
    
    def _decrypt_password(self) -> str:
        """Decrypt password using Fernet."""
        if not self.smtp_password_encrypted:
            return ''
        try:
            cipher = self._get_cipher()
            decrypted = cipher.decrypt(self.smtp_password_encrypted.encode())
            return decrypted.decode()
        except (InvalidToken, Exception) as e:
            logger.error(f"Failed to decrypt email password: {e}")
            return ''
    
    def get_email_backend_config(self) -> dict:
        """
        Get email backend configuration as a dictionary.
        Decrypts password on the fly.
        
        Returns:
            Dictionary with EMAIL_* settings suitable for Django email backend
        """
        return {
            'EMAIL_BACKEND': 'invoicing_app.core.email_backend.DynamicEmailBackend',
            'EMAIL_HOST': self.smtp_host,
            'EMAIL_PORT': self.smtp_port,
            'EMAIL_HOST_USER': self.smtp_username,
            'EMAIL_HOST_PASSWORD': self._decrypt_password(),
            'EMAIL_USE_TLS': self.smtp_use_tls,
            'EMAIL_USE_SSL': self.smtp_use_ssl,
            'DEFAULT_FROM_EMAIL': self.from_email,
        }
    
    def get_event_config(self) -> dict:
        """
        Get email event toggles configuration.
        
        Returns:
            Dictionary with email event settings
        """
        return {
            'enable_invoice_created': self.enable_invoice_created,
            'enable_invoice_sent': self.enable_invoice_sent,
            'enable_payment_received': self.enable_payment_received,
            'enable_payment_overdue': self.enable_payment_overdue,
            'send_to_client_on_creation': self.send_to_client_on_creation,
            'days_before_due_reminder': self.days_before_due_reminder,
        }
    
    def should_send_invoice_email(self, event_type: str) -> bool:
        """
        Check if email should be sent for an invoice event.
        
        Args:
            event_type: 'created', 'sent'
        
        Returns:
            Boolean indicating if email should be sent
        """
        if event_type == 'created':
            return self.enable_invoice_created and self.send_to_client_on_creation
        elif event_type == 'sent':
            return self.enable_invoice_sent
        return False
    
    def should_send_payment_email(self, event_type: str) -> bool:
        """
        Check if email should be sent for a payment event.
        
        Args:
            event_type: 'received', 'overdue'
        
        Returns:
            Boolean indicating if email should be sent
        """
        if event_type == 'received':
            return self.enable_payment_received
        elif event_type == 'overdue':
            return self.enable_payment_overdue
        return False
    
    def mark_test_success(self):
        """Mark email configuration as successfully tested."""
        self.is_configured = True
        self.last_tested_at = timezone.now()
        self.last_test_status = 'success'
        self.last_test_error = ''
        self.save()
    
    def mark_test_failed(self, error_message: str):
        """
        Mark email configuration as failed test.
        
        Args:
            error_message: Description of the error that occurred
        """
        self.is_configured = False
        self.last_tested_at = timezone.now()
        self.last_test_status = 'failed'
        self.last_test_error = error_message[:500]  # Store first 500 chars
        self.save()

class FAQ(BaseModel):
    """
    Frequently Asked Questions.
    """
    CATEGORY_CHOICES = [
        ('invoicing', 'Invoicing & Quotations'),
        ('payments', 'Payments'),
        ('clients', 'Client Management'),
        ('products', 'Products & Services'),
        ('reports', 'Reports & Analysis'),
        ('settings', 'Settings & Configuration'),
        ('technical', 'Technical Issues'),
        ('other', 'Other'),
    ]

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        db_index=True,
        help_text="FAQ category"
    )
    question = models.CharField(
        max_length=500,
        help_text="The frequently asked question"
    )
    answer = models.TextField(
        help_text="Detailed answer to the question"
    )
    order = models.SmallIntegerField(
        default=0,
        help_text="Display order within category"
    )
    views_count = models.IntegerField(
        default=0,
        help_text="Number of times this FAQ has been viewed"
    )
    helpful_yes = models.IntegerField(
        default=0,
        help_text="Number of 'helpful' votes"
    )
    helpful_no = models.IntegerField(
        default=0,
        help_text="Number of 'not helpful' votes"
    )

    class Meta:
        db_table = 'core_faq'
        ordering = ['category', 'order', '-created_at']
        indexes = [
            models.Index(fields=['category', 'order']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.question[:50]}..."

    def increment_views(self):
        """Increment view count."""
        self.views_count += 1
        self.save(update_fields=['views_count'])

    def mark_helpful(self, helpful=True):
        """Mark as helpful or not helpful."""
        if helpful:
            self.helpful_yes += 1
        else:
            self.helpful_no += 1
        self.save(update_fields=['helpful_yes', 'helpful_no'])


class HelpArticle(BaseModel):
    """
    Help documentation articles for detailed guides and tutorials.
    """
    CATEGORY_CHOICES = [
        ('getting-started', 'Getting Started'),
        ('invoicing', 'Invoicing & Quotations'),
        ('payments', 'Payments'),
        ('clients', 'Client Management'),
        ('products', 'Products & Services'),
        ('reports', 'Reports & Analysis'),
        ('settings', 'Settings & Configuration'),
        ('integration', 'Integrations'),
        ('api', 'API Documentation'),
        ('troubleshooting', 'Troubleshooting'),
    ]

    title = models.CharField(
        max_length=300,
        db_index=True,
        help_text="Article title"
    )
    slug = models.SlugField(
        unique=True,
        db_index=True,
        help_text="URL-friendly identifier"
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        db_index=True,
        help_text="Help article category"
    )
    content = models.TextField(
        help_text="Full article content (supports HTML/Markdown)"
    )
    excerpt = models.CharField(
        max_length=500,
        blank=True,
        help_text="Short preview of article content"
    )
    author = models.CharField(
        max_length=100,
        default='Admin',
        help_text="Article author"
    )
    views_count = models.IntegerField(
        default=0,
        help_text="Number of times this article has been viewed"
    )
    featured = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Featured article on help homepage"
    )
    order = models.SmallIntegerField(
        default=0,
        help_text="Display order within category"
    )
    tags = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated tags for search"
    )

    class Meta:
        db_table = 'core_help_article'
        ordering = ['-featured', 'category', 'order', '-created_at']
        indexes = [
            models.Index(fields=['category', 'order']),
            models.Index(fields=['featured', '-created_at']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.title

    def increment_views(self):
        """Increment view count."""
        self.views_count += 1
        self.save(update_fields=['views_count'])


class SupportTicket(BaseModel):
    """
    User support request tickets.
    """
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    ticket_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Unique ticket identifier"
    )
    name = models.CharField(
        max_length=200,
        help_text="Submitter's name"
    )
    email = models.EmailField(
        db_index=True,
        help_text="Submitter's email address"
    )
    subject = models.CharField(
        max_length=300,
        help_text="Support ticket subject"
    )
    message = models.TextField(
        help_text="Detailed support request message"
    )
    category = models.CharField(
        max_length=50,
        default='general',
        help_text="Support ticket category"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        help_text="Ticket priority level"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='open',
        db_index=True,
        help_text="Current ticket status"
    )
    assigned_to = models.CharField(
        max_length=100,
        blank=True,
        help_text="Team member assigned to ticket"
    )
    resolution_notes = models.TextField(
        blank=True,
        help_text="Internal notes and resolution details"
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the ticket was resolved"
    )
    attachment_url = models.URLField(
        blank=True,
        help_text="URL to any attachment"
    )

    class Meta:
        db_table = 'core_support_ticket'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['priority', 'status']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.ticket_number} - {self.subject}"

    def save(self, *args, **kwargs):
        """Generate ticket number on first save."""
        if not self.ticket_number:
            # Generate ticket number: TICKET-20260001, etc.
            from django.utils import timezone
            date_str = timezone.now().strftime('%y%m%d')
            count = SupportTicket.objects.filter(
                ticket_number__startswith=f'TICKET-{date_str}'
            ).count() + 1
            self.ticket_number = f'TICKET-{date_str}{count:04d}'
        super().save(*args, **kwargs)

    def mark_resolved(self, resolution_notes=''):
        """Mark ticket as resolved."""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        if resolution_notes:
            self.resolution_notes = resolution_notes
        self.save()

    def mark_closed(self):
        """Mark ticket as closed."""
        self.status = 'closed'
        self.save()


class SavedFilter(TimeStampedModel):
    """
    Saved filter presets for advanced search.
    Allows users to save and reuse common filter combinations.
    """
    id = models.BigAutoField(primary_key=True)
    
    # Basic Info
    name = models.CharField(
        max_length=255,
        help_text="Name of this filter preset (e.g., 'Unpaid Invoices Over 30 Days')"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description of what this filter shows"
    )
    
    # Filter Scope
    filter_type = models.CharField(
        max_length=50,
        choices=[
            ('invoice', 'Invoices'),
            ('payment', 'Payments'),
            ('client', 'Clients'),
            ('quotation', 'Quotations'),
            ('expense', 'Expenses'),
        ],
        db_index=True,
        help_text="What entity type this filter applies to"
    )
    
    # Filter Criteria (stored as JSON for flexibility)
    filter_criteria = models.JSONField(
        default=dict,
        help_text="Filter conditions as JSON (e.g., {'status': 'unpaid', 'days_overdue': {'gte': 30}})"
    )
    
    # Ownership & Sharing
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_filters',
        help_text="User who created this filter"
    )
    is_global = models.BooleanField(
        default=False,
        help_text="If True, visible to all users; if False, only visible to creator"
    )
    
    # Sorting & Display
    sort_by = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Field to sort by (e.g., 'invoice_date', '-amount')"
    )
    
    # Usage Tracking
    last_used = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last time this filter was applied"
    )
    use_count = models.IntegerField(
        default=0,
        help_text="Number of times this filter has been used"
    )
    
    class Meta:
        db_table = 'core_savedfilter'
        ordering = ['-last_used', '-created_at']
        indexes = [
            models.Index(fields=['created_by', 'filter_type']),
            models.Index(fields=['filter_type', 'is_global']),
            models.Index(fields=['-last_used']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.filter_type})"
    
    def get_url_params(self):
        """Convert filter criteria to URL query parameters."""
        params = {}
        for key, value in self.filter_criteria.items():
            if isinstance(value, dict):
                # Handle range operators like {'gte': 100, 'lte': 500}
                for op, val in value.items():
                    params[f"{key}__{op}"] = val
            else:
                params[key] = value
        return params
    
    def record_usage(self):
        """Update last_used timestamp and increment use_count."""
        self.last_used = timezone.now()
        self.use_count += 1
        self.save(update_fields=['last_used', 'use_count'])
    
    @classmethod
    def get_user_filters(cls, user, filter_type):
        """Get available filters for a user (personal + global)."""
        return cls.objects.filter(
            filter_type=filter_type
        ).filter(
            models.Q(created_by=user) | models.Q(is_global=True)
        ).order_by('-last_used', 'name')
