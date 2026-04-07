"""Forms for Financials module - Tax Liability and Revenue tracking."""

from django import forms
from datetime import datetime
from .models import TaxLiability, RevenueCollection


class TaxLiabilityForm(forms.ModelForm):
    """Form for creating/editing tax liabilities with remittance tracking."""

    class Meta:
        model = TaxLiability
        fields = [
            "financial_period",
            "tax_type",
            "total_revenue",
            "total_tax_collected",
            "due_date",
            "remitted_date",
            "remittance_reference",
            "status",
            "penalties",
            "discounts",
            "final_liability",
            "notes",
        ]
        widgets = {
            "financial_period": forms.Select(
                attrs={
                    "class": "form-control",
                    "required": True,
                }
            ),
            "tax_type": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "VAT, Income Tax, etc.",
                    "required": True,
                }
            ),
            "total_revenue": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "0.00",
                }
            ),
            "total_tax_collected": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "0.00",
                    "required": True,
                }
            ),
            "due_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                    "required": True,
                }
            ),
            "remitted_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                    "help_text": "Leave blank if not remitted yet",
                }
            ),
            "remittance_reference": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Tax office receipt/reference number",
                    "help_text": "Reference from tax authority confirming remittance",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-control",
                    "required": True,
                }
            ),
            "penalties": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "0.00",
                    "help_text": "Late payment penalties or additional charges",
                }
            ),
            "discounts": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "0.00",
                    "help_text": "Tax discounts or incentives applied",
                }
            ),
            "final_liability": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Additional notes about this tax liability",
                }
            ),
        }

    def clean(self):
        """Validate form data."""
        cleaned_data = super().clean()
        due_date = cleaned_data.get("due_date")
        remitted_date = cleaned_data.get("remitted_date")
        status = cleaned_data.get("status")

        # If remitted, remitted_date should be set
        if status == "remitted" and not remitted_date:
            self.add_error(
                "remitted_date",
                "Remittance date is required when status is 'Remitted'.",
            )

        # Remitted date should not be after today
        if remitted_date and remitted_date > datetime.now().date():
            self.add_error("remitted_date", "Remittance date cannot be in the future.")

        # Remitted date should be on or after due date
        if remitted_date and due_date and remitted_date < due_date:
            self.add_error(
                "remitted_date",
                "Remittance date should be on or after the due date.",
            )

        return cleaned_data


class RevenueCollectionForm(forms.ModelForm):
    """Form for recording individual revenue/tax collections."""

    class Meta:
        model = RevenueCollection
        fields = [
            "invoice",
            "financial_period",
            "revenue_amount",
            "tax_amount",
            "total_amount",
            "collected_date",
            "tax_type",
        ]
        widgets = {
            "invoice": forms.Select(
                attrs={
                    "class": "form-control",
                    "required": True,
                }
            ),
            "financial_period": forms.Select(
                attrs={
                    "class": "form-control",
                    "required": True,
                }
            ),
            "revenue_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "0.00",
                    "required": True,
                }
            ),
            "tax_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "0.00",
                    "help_text": "Tax amount from this collection",
                }
            ),
            "total_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "0.00",
                    "required": True,
                }
            ),
            "collected_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                    "required": True,
                }
            ),
            "tax_type": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "VAT, Withholding, etc.",
                    "required": True,
                }
            ),
        }

    def clean(self):
        """Validate form data."""
        cleaned_data = super().clean()
        revenue_amount = cleaned_data.get("revenue_amount")
        tax_amount = cleaned_data.get("tax_amount")
        total_amount = cleaned_data.get("total_amount")

        # Validate that total = revenue + tax
        if revenue_amount and tax_amount and total_amount:
            expected_total = revenue_amount + tax_amount
            if total_amount != expected_total:
                self.add_error(
                    "total_amount",
                    f"Total amount should be {expected_total} (revenue + tax).",
                )

        return cleaned_data


class TaxLiabilityFilterForm(forms.Form):
    """Form for filtering tax liabilities."""

    STATUS_CHOICES = [
        ("", "--- All Statuses ---"),
        ("pending", "Pending"),
        ("due_soon", "Due Soon"),
        ("overdue", "Overdue"),
        ("remitted", "Remitted"),
        ("disputed", "Disputed"),
    ]

    TAX_TYPE_CHOICES = [
        ("", "--- All Tax Types ---"),
        ("VAT", "VAT"),
        ("INCOME_TAX", "Income Tax"),
        ("OTHER", "Other"),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    tax_type = forms.ChoiceField(
        choices=TAX_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    due_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
                "placeholder": "From date",
            }
        ),
    )

    due_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
                "placeholder": "To date",
            }
        ),
    )

    min_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
                "placeholder": "Minimum amount",
            }
        ),
    )

    max_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
                "placeholder": "Maximum amount",
            }
        ),
    )
