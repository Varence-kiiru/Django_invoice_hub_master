"""
Forms for Quote management.
"""
from django import forms
from django.forms import inlineformset_factory
from .models import Quote, QuoteLineItem


class QuoteForm(forms.ModelForm):
    """Form for creating and editing quotes."""

    class Meta:
        model = Quote
        fields = [
            'client', 'quote_date', 'valid_until', 'description', 'currency'
        ]
        widgets = {
            'client': forms.Select(attrs={
                'class': 'form-control'
            }),
            'quote_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'valid_until': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Quote description/terms (optional)'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def clean_valid_until(self):
        """Validate valid_until date is after quote date."""
        quote_date = self.cleaned_data.get('quote_date')
        valid_until = self.cleaned_data.get('valid_until')

        if quote_date and valid_until and valid_until < quote_date:
            raise forms.ValidationError(
                'Valid until date must be after or equal to quote date.'
            )
        return valid_until

    def clean_client(self):
        """Validate client is active."""
        client = self.cleaned_data.get('client')
        if client and not client.is_active:
            raise forms.ValidationError('Cannot create quote for inactive client.')
        return client


class QuoteLineItemForm(forms.ModelForm):
    """Form for quote line items."""

    class Meta:
        model = QuoteLineItem
        fields = [
            'product', 'description', 'quantity', 'unit_price', 'tax_rate'
        ]
        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Item description'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Qty'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Unit price'
            }),
            'tax_rate': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def clean_quantity(self):
        """Validate quantity is positive."""
        quantity = self.cleaned_data.get('quantity', 0)
        if quantity <= 0:
            raise forms.ValidationError('Quantity must be greater than 0.')
        return quantity

    def clean_unit_price(self):
        """Validate unit price is non-negative."""
        price = self.cleaned_data.get('unit_price', 0)
        if price < 0:
            raise forms.ValidationError('Unit price cannot be negative.')
        return price


# Formset for managing multiple line items
QuoteLineItemFormSet = inlineformset_factory(
    Quote,
    QuoteLineItem,
    form=QuoteLineItemForm,
    extra=1,
    can_delete=True
)
