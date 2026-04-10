"""Forms for Client management."""

from django import forms
from .models import Client, ClientAddress, ClientContact


class ClientForm(forms.ModelForm):
    """Form for creating and editing clients."""

    class Meta:
        model = Client
        fields = [
            "name",
            "email",
            "phone",
            "client_type",
            "tax_id",
            "business_registration_number",
            "payment_terms_days",
            "currency",
            "credit_limit",
            "notes",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Client name"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Email address"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Phone number"}
            ),
            "client_type": forms.Select(attrs={"class": "form-control"}),
            "tax_id": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Tax ID / PIN"}
            ),
            "business_registration_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Business registration number",
                }
            ),
            "payment_terms_days": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "30",
                    "min": "0",
                    "max": "365",
                }
            ),
            "currency": forms.TextInput(
                attrs={"class": "form-control", "readonly": True, "disabled": True}
            ),
            "credit_limit": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "0.00", "step": "0.01"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Additional notes",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set currency to system default and make it read-only
        from invoicing_app.core.models import CompanySettings

        company_settings = CompanySettings.get_settings()
        self.fields["currency"].initial = company_settings.default_currency
        self.fields["currency"].disabled = True
        # Override any existing value to ensure it's always the system default
        if not self.instance.pk:  # For new clients, set to default
            self.initial["currency"] = company_settings.default_currency

    def clean_email(self):
        """Validate email uniqueness."""
        email = self.cleaned_data.get("email")
        if email:
            # Allow same email for same client during edit
            qs = Client.objects.filter(email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("A client with this email already exists.")
        return email

    def clean_name(self):
        """Validate client name is not empty."""
        name = self.cleaned_data.get("name")
        if not name or not name.strip():
            raise forms.ValidationError("Client name is required.")
        return name.strip()

    def clean_phone(self):
        """Validate phone number format."""
        phone = self.cleaned_data.get("phone")
        if phone:
            # Basic phone validation - allow common formats
            import re

            phone_pattern = re.compile(r"^[\+]?[\d\s\-\(\)\.]{7,15}$")
            if not phone_pattern.match(phone):
                raise forms.ValidationError("Please enter a valid phone number.")
        return phone

    def clean_tax_id(self):
        """Validate tax ID format."""
        tax_id = self.cleaned_data.get("tax_id", "")
        if tax_id and len(tax_id) < 3:
            raise forms.ValidationError("Tax ID must be at least 3 characters.")
        return tax_id

    def clean_payment_terms_days(self):
        """Validate payment terms."""
        days = self.cleaned_data.get("payment_terms_days", 0)
        if days < 0 or days > 365:
            raise forms.ValidationError("Payment terms must be between 0 and 365 days.")
        return days

    def clean(self):
        """Ensure currency is always set to system default."""
        cleaned_data = super().clean()
        from invoicing_app.core.models import CompanySettings

        company_settings = CompanySettings.get_settings()
        # Force currency to system default regardless of form input
        cleaned_data["currency"] = company_settings.default_currency
        return cleaned_data


class ClientAddressForm(forms.ModelForm):
    """Form for client addresses."""

    class Meta:
        model = ClientAddress
        fields = [
            "address_type",
            "street_1",
            "street_2",
            "city",
            "state_province",
            "postal_code",
            "country",
        ]
        widgets = {
            "address_type": forms.Select(attrs={"class": "form-control"}),
            "street_1": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Street address"}
            ),
            "street_2": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Street address line 2 (optional)",
                }
            ),
            "city": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "City"}
            ),
            "state_province": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "State/Province"}
            ),
            "postal_code": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Postal code"}
            ),
            "country": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Country"}
            ),
        }


class ClientContactForm(forms.ModelForm):
    """Form for client contacts."""

    class Meta:
        model = ClientContact
        fields = ["name", "title", "email", "phone", "is_primary"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Contact name"}
            ),
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Job title"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Email"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Phone"}
            ),
            "is_primary": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
