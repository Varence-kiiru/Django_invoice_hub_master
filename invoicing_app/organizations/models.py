"""
Organization and subscription models for multi-tenant SaaS.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from invoicing_app.core.models import BaseModel
import uuid


class Organization(BaseModel):
    """
    Multi-tenant organization model.
    Each organization is a completely isolated workspace with its own data.
    """
    name = models.CharField(
        max_length=255,
        help_text="Organization/Company name"
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="URL-friendly identifier (e.g., 'acme-corp')"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Organization description"
    )
    website = models.URLField(
        blank=True,
        null=True,
        help_text="Organization's website"
    )
    logo = models.ImageField(
        upload_to='organization_logos/',
        blank=True,
        null=True,
        help_text="Organization logo"
    )
    
    # Billing & Plan Info
    plan = models.CharField(
        max_length=50,
        choices=[
            ('free', 'Free'),
            ('starter', 'Starter'),
            ('professional', 'Professional'),
            ('enterprise', 'Enterprise'),
        ],
        default='free',
        db_index=True,
        help_text="Current subscription plan"
    )
    
    # Contact info
    admin_email = models.EmailField(
        help_text="Primary admin email for this organization"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Organization contact phone"
    )
    
    # Usage tracking
    invoice_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total invoices created (for usage tracking)"
    )
    user_count = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Number of active users in organization"
    )
    
    # Dates
    subscription_started = models.DateTimeField(
        auto_now_add=True,
        help_text="When organization was created"
    )
    subscription_renew_date = models.DateField(
        blank=True,
        null=True,
        help_text="When current subscription renews"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('suspended', 'Suspended - Payment Issue'),
            ('cancelled', 'Cancelled'),
            ('trial', 'Trial'),
        ],
        default='active',
        db_index=True,
        help_text="Organization status"
    )
    
    # Stripe integration
    stripe_customer_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        db_index=True,
        help_text="Stripe Customer ID for billing"
    )
    stripe_subscription_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        db_index=True,
        help_text="Stripe Subscription ID"
    )
    
    # Feature flags
    enable_api_access = models.BooleanField(
        default=False,
        help_text="Allow API access for this organization"
    )
    enable_custom_branding = models.BooleanField(
        default=False,
        help_text="Allow custom company branding (premium feature)"
    )
    enable_advanced_analytics = models.BooleanField(
        default=False,
        help_text="Enable advanced analytics (premium feature)"
    )
    enable_api_webhooks = models.BooleanField(
        default=False,
        help_text="Enable webhook notifications (premium feature)"
    )
    
    # API Key for integrations
    api_key = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        default=None,
        blank=True,
        null=True,
        help_text="API key for external integrations"
    )
    
    class Meta:
        db_table = 'organizations_organization'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['plan']),
            models.Index(fields=['status']),
            models.Index(fields=['stripe_customer_id']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.plan})"
    
    def save(self, *args, **kwargs):
        # Auto-generate API key if not present
        if not self.api_key:
            self.api_key = self._generate_api_key()
        super().save(*args, **kwargs)
    
    @staticmethod
    def _generate_api_key():
        """Generate a unique API key for organization"""
        return str(uuid.uuid4()).replace('-', '') + str(uuid.uuid4()).replace('-', '')
    
    def get_plan_limits(self):
        """Get plan limits for feature gating"""
        limits = {
            'free': {
                'max_users': 1,
                'max_invoices': 50,
                'max_products': 20,
                'max_clients': 10,
                'features': ['basic_invoicing']
            },
            'starter': {
                'max_users': 5,
                'max_invoices': 1000,
                'max_products': 500,
                'max_clients': 500,
                'features': ['basic_invoicing', 'delivery_tracking', 'expense_tracking']
            },
            'professional': {
                'max_users': 25,
                'max_invoices': 50000,
                'max_products': 10000,
                'max_clients': 10000,
                'features': ['basic_invoicing', 'delivery_tracking', 'expense_tracking', 'api_access', 'custom_branding', 'analytics']
            },
            'enterprise': {
                'max_users': float('inf'),
                'max_invoices': float('inf'),
                'max_products': float('inf'),
                'max_clients': float('inf'),
                'features': ['all']
            }
        }
        return limits.get(self.plan, limits['free'])


class OrganizationMember(BaseModel):
    """
    Tracks users that belong to an organization with their role.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='members',
        db_index=True,
        help_text="Organization this user belongs to"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='org_memberships',
        db_index=True,
        help_text="User account"
    )
    role = models.CharField(
        max_length=20,
        choices=[
            ('owner', 'Owner'),
            ('admin', 'Admin'),
            ('manager', 'Manager'),
            ('accountant', 'Accountant'),
            ('staff', 'Staff'),
            ('viewer', 'Viewer'),
        ],
        default='staff',
        help_text="User's role in this organization"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Is this the primary owner account?"
    )
    joined_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When user joined organization"
    )
    
    class Meta:
        db_table = 'organizations_member'
        unique_together = [['organization', 'user']]
        ordering = ['-is_primary', '-joined_at']
        indexes = [
            models.Index(fields=['organization', 'user']),
            models.Index(fields=['organization', 'role']),
        ]
    
    def __str__(self):
        return f"{self.user.email} ({self.role}) @ {self.organization.name}"


class Subscription(BaseModel):
    """
    Subscription and billing history tracking.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('past_due', 'Past Due'),
        ('trialing', 'Trialing'),
    ]
    
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name='subscription',
        help_text="Organization this subscription belongs to"
    )
    plan = models.CharField(
        max_length=50,
        help_text="Plan name (free, starter, professional, enterprise)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True,
        help_text="Subscription status"
    )
    
    # Dates
    start_date = models.DateField(
        auto_now_add=True,
        help_text="When subscription started"
    )
    current_period_start = models.DateField(
        help_text="Current billing period start"
    )
    current_period_end = models.DateField(
        help_text="Current billing period end"
    )
    trial_end = models.DateField(
        blank=True,
        null=True,
        help_text="When trial period ends (if applicable)"
    )
    
    # Pricing
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Monthly subscription amount in USD"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency code (USD, EUR, GBP, etc.)"
    )
    
    # Billing
    auto_renew = models.BooleanField(
        default=True,
        help_text="Auto-renew subscription at end of period"
    )
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ('credit_card', 'Credit Card'),
            ('debit_card', 'Debit Card'),
            ('bank_transfer', 'Bank Transfer'),
            ('paypal', 'PayPal'),
            ('stripe', 'Stripe'),
        ],
        default='stripe',
        help_text="Payment method for renewal"
    )
    
    class Meta:
        db_table = 'organizations_subscription'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.organization.name} - {self.plan} ({self.status})"
    
    @property
    def is_active(self):
        """Check if subscription is currently active"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.status in ['active', 'trialing'] and today < self.current_period_end


class Invoice(BaseModel):
    """
    Billing invoice tracking for subscription payments.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='billing_invoices',
        help_text="Organization this invoice is for"
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        help_text="Subscription this invoice is for"
    )
    
    # Invoice details
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Billing invoice number (e.g., INV-2025-0001)"
    )
    stripe_invoice_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        help_text="Stripe Invoice ID"
    )
    
    # Amounts
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Invoice amount in cents/dollars"
    )
    tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Tax amount"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True,
        help_text="Invoice status"
    )
    
    # Dates
    issue_date = models.DateField(
        auto_now_add=True,
        help_text="When invoice was issued"
    )
    due_date = models.DateField(
        help_text="Payment due date"
    )
    paid_date = models.DateField(
        blank=True,
        null=True,
        help_text="When payment was received"
    )
    
    # Description
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Invoice description/line items"
    )
    
    class Meta:
        db_table = 'organizations_billing_invoice'
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['invoice_number']),
        ]
    
    def __str__(self):
        return f"{self.invoice_number} - {self.organization.name}"
