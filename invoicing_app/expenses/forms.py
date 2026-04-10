"""
Forms for expense tracking.
Handles validation and input for expenses, vendors, and categories.
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import Expense, Vendor, ExpenseCategory, ExpenseBudget
from invoicing_app.core.models import CompanySettings


class ExpenseCategoryForm(forms.ModelForm):
    """Form for creating and editing expense categories."""

    class Meta:
        model = ExpenseCategory
        fields = ["name", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., Office Supplies, Travel, Utilities",
                    "required": True,
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Description of this expense category",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }


class VendorForm(forms.ModelForm):
    """Form for creating and editing vendors/suppliers."""

    class Meta:
        model = Vendor
        fields = [
            "name",
            "contact_email",
            "contact_phone",
            "address",
            "payment_terms",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Vendor/Supplier name",
                    "required": True,
                }
            ),
            "contact_email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "vendor@example.com",
                }
            ),
            "contact_phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "+1 (555) 123-4567",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Physical address",
                }
            ),
            "payment_terms": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., Net 30, Due on Receipt",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def clean_contact_email(self):
        """Validate email field."""
        email = self.cleaned_data.get("contact_email")
        if email:
            # Check for duplicate emails (excluding current vendor)
            qs = Vendor.objects.filter(contact_email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("A vendor with this email already exists.")
        return email


class ExpenseForm(forms.ModelForm):
    """Form for creating and editing expenses."""

    class Meta:
        model = Expense
        fields = [
            "description",
            "category",
            "vendor",
            "amount",
            "currency",
            "expense_date",
            "payment_method",
            "status",
            "receipt_file",
            "is_reimbursable",
            "notes",
        ]
        widgets = {
            "description": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Description of the expense",
                    "required": True,
                }
            ),
            "category": forms.Select(
                attrs={
                    "class": "form-control",
                    "required": True,
                }
            ),
            "vendor": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0.00",
                    "step": "0.01",
                    "min": "0.01",
                    "required": True,
                }
            ),
            "currency": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "expense_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                    "required": True,
                }
            ),
            "payment_method": forms.Select(
                attrs={
                    "class": "form-control",
                    "required": True,
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "receipt_file": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf,.jpg,.jpeg,.png,.doc,.docx",
                }
            ),
            "is_reimbursable": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Additional notes or details",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active categories
        self.fields["category"].queryset = ExpenseCategory.objects.filter(
            is_active=True
        )
        # Only show active vendors
        self.fields["vendor"].queryset = Vendor.objects.filter(is_active=True)

        # Set currency choices from CompanySettings
        try:
            settings = CompanySettings.get_settings()
            currency_choices = settings.CURRENCY_CHOICES
            self.fields["currency"].widget = forms.Select(
                choices=currency_choices, attrs={"class": "form-control"}
            )
        except Exception:
            # Fallback to default if settings not available
            self.fields["currency"].widget = forms.Select(
                choices=[("KES", "Kenyan Shilling (KES)"), ("USD", "US Dollar (USD)")],
                attrs={"class": "form-control"},
            )

        # If editing an existing expense that is paid, disable critical fields
        if self.instance and self.instance.pk and self.instance.status == "paid":
            # Disable fields that shouldn't be changed for paid expenses
            locked_fields = [
                "description",
                "category",
                "vendor",
                "amount",
                "currency",
                "expense_date",
                "payment_method",
            ]
            for field_name in locked_fields:
                if field_name in self.fields:
                    self.fields[field_name].disabled = True
                    self.fields[field_name].widget.attrs["readonly"] = True
                    self.fields[field_name].help_text = (
                        "This field is locked for paid expenses."
                    )

    def clean(self):
        """Validate form data and prevent invalid status transitions."""
        cleaned_data = super().clean()
        amount = cleaned_data.get("amount")
        new_status = cleaned_data.get("status")

        if amount and amount <= 0:
            raise ValidationError("Expense amount must be greater than 0.")

        # If editing an existing expense, validate status transitions
        if self.instance and self.instance.pk:
            current_status = self.instance.status

            # Prevent changing status of paid expenses
            if current_status == "paid":
                if new_status != current_status:
                    raise ValidationError(
                        "Cannot change the status of a paid expense. "
                        "Paid expenses are locked and cannot be modified."
                    )

            # Validate valid status transitions
            valid_transitions = {
                "draft": ["draft", "submitted"],  # Draft can go to submitted
                "submitted": [
                    "draft",
                    "submitted",
                    "approved",
                    "rejected",
                ],  # Submitted can go back to draft, stay, or be approved/rejected
                "approved": [
                    "draft",
                    "approved",
                    "paid",
                ],  # Approved can go back to draft, stay, or be paid
                "rejected": [
                    "draft",
                    "rejected",
                ],  # Rejected can only go back to draft or stay
                "paid": ["paid"],  # Paid cannot change
            }

            if current_status in valid_transitions:
                if new_status not in valid_transitions[current_status]:
                    raise ValidationError(
                        f"Cannot transition from {current_status} to {new_status}. "
                        f"Valid transitions from {current_status}: {', '.join(valid_transitions[current_status])}"
                    )

        return cleaned_data


class ExpenseBudgetForm(forms.ModelForm):
    """Form for setting and managing expense budgets."""

    class Meta:
        model = ExpenseBudget
        fields = ["category", "monthly_limit", "annual_limit", "alert_threshold"]
        widgets = {
            "category": forms.Select(
                attrs={
                    "class": "form-control",
                    "required": True,
                }
            ),
            "monthly_limit": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0.00",
                    "step": "0.01",
                    "min": "0",
                    "required": True,
                }
            ),
            "annual_limit": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0.00",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "alert_threshold": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., 80 (for 80%)",
                    "step": "1",
                    "min": "0",
                    "max": "100",
                    "value": "80",
                }
            ),
        }

    def clean(self):
        """Validate budget amounts."""
        cleaned_data = super().clean()
        monthly_limit = cleaned_data.get("monthly_limit")

        if monthly_limit and monthly_limit <= 0:
            raise ValidationError("Monthly limit must be greater than 0.")

        return cleaned_data
