"""
Client/customer models.
"""
from django.db import models
from invoicing_app.core.models import BaseModel, ActiveModel


class Client(ActiveModel):
    """
    Customer/business entity.
    """
    CLIENT_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('business', 'Business'),
    ]

    CURRENCY_CHOICES = [
        ('KES', 'Kenyan Shilling'),
        ('USD', 'US Dollar'),
    ]

    name = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Client's business or full name"
    )
    client_type = models.CharField(
        max_length=20,
        choices=CLIENT_TYPE_CHOICES,
        default='individual',
        db_index=True,
        help_text="Individual or business for KRA classification"
    )
    business_registration_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="Business registration number if applicable"
    )
    tax_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="KRA PIN or VAT number"
    )
    email = models.EmailField(
        blank=True,
        null=True,
        help_text="Client's primary email"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Client's primary phone"
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='KES',
        help_text="Default currency for invoices"
    )
    default_tax_rate = models.ForeignKey(
        'taxes.TaxRate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Default VAT rate for this client"
    )
    payment_terms_days = models.IntegerField(
        default=30,
        help_text="Invoice due-in days (payment terms)"
    )
    credit_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Credit limit for future credit management"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Internal notes about client"
    )
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_clients',
        help_text="User who created this client"
    )

    class Meta:
        db_table = 'clients_client'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['tax_id']),
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
            models.Index(fields=['client_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.client_type})"

    def get_currency_symbol(self):
        """Get the currency symbol for this client's currency."""
        currency_symbols = {
            'KES': 'Ksh',
            'USD': '$',
            'EUR': '€',
        }
        return currency_symbols.get(self.currency, self.currency)


class ClientAddress(models.Model):
    """
    Client addresses (billing, shipping, etc.).
    One-to-many relationship with Client.
    """
    ADDRESS_TYPE_CHOICES = [
        ('billing', 'Billing Address'),
        ('shipping', 'Shipping Address'),
        ('other', 'Other'),
    ]

    id = models.BigAutoField(primary_key=True)
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='addresses',
        help_text="Client this address belongs to"
    )
    address_type = models.CharField(
        max_length=20,
        choices=ADDRESS_TYPE_CHOICES,
        default='billing',
        help_text="Type of address"
    )
    street_1 = models.CharField(
        max_length=255,
        help_text="Street line 1"
    )
    street_2 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Street line 2 (apartment, suite, etc.)"
    )
    city = models.CharField(
        max_length=100,
        help_text="City"
    )
    state_province = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="State or province"
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Postal code"
    )
    country = models.CharField(
        max_length=100,
        default='Kenya',
        help_text="Country"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Is this the primary address of this type?"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clients_clientaddress'
        indexes = [
            models.Index(fields=['client', 'address_type']),
            models.Index(fields=['client', 'is_primary']),
        ]

    def __str__(self):
        return f"{self.client.name} - {self.get_address_type_display()}"


class ClientContact(models.Model):
    """
    Client contacts (people at the client organization).
    One-to-many relationship with Client.
    """
    id = models.BigAutoField(primary_key=True)
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='contacts',
        help_text="Client this contact belongs to"
    )
    name = models.CharField(
        max_length=255,
        help_text="Contact person's name"
    )
    title = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Job title (Finance Manager, etc.)"
    )
    email = models.EmailField(
        blank=True,
        null=True,
        help_text="Contact email"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Contact phone"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Is this the primary contact?"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes about this contact"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clients_clientcontact'
        indexes = [
            models.Index(fields=['client']),
            models.Index(fields=['client', 'is_primary']),
        ]

    def __str__(self):
        return f"{self.name} ({self.client.name})"
