"""Forms for Invoice and Payment management."""
from django import forms
from django.forms import inlineformset_factory
from invoicing_app.invoices.models import Invoice, InvoiceLineItem
from invoicing_app.payments.models import Payment
from invoicing_app.clients.models import Client
from invoicing_app.products.models import Product
from invoicing_app.taxes.models import TaxRate


class InvoiceForm(forms.ModelForm):
    """Form for creating and editing invoices."""
    
    class Meta:
        model = Invoice
        fields = [
            'client', 'invoice_date', 'due_date', 'description', 'currency'
        ]
        widgets = {
            'client': forms.Select(attrs={
                'class': 'form-control'
            }),
            'invoice_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Invoice description (optional)'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def clean_due_date(self):
        """Validate due date is after invoice date."""
        invoice_date = self.cleaned_data.get('invoice_date')
        due_date = self.cleaned_data.get('due_date')
        
        if invoice_date and due_date and due_date < invoice_date:
            raise forms.ValidationError('Due date must be after invoice date.')
        return due_date
    
    def clean_client(self):
        """Validate client is active."""
        client = self.cleaned_data.get('client')
        if client and not client.is_active:
            raise forms.ValidationError('Cannot create invoice for inactive client.')
        return client


class InvoiceLineItemForm(forms.ModelForm):
    """Form for invoice line items."""
    
    class Meta:
        model = InvoiceLineItem
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
InvoiceLineItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceLineItem,
    form=InvoiceLineItemForm,
    extra=1,
    can_delete=True
)


class PaymentForm(forms.ModelForm):
    """Form for recording payments."""
    
    class Meta:
        model = Payment
        fields = [
            'invoice', 'amount', 'payment_method', 'payment_date', 
            'transaction_reference', 'notes'
        ]
        widgets = {
            'invoice': forms.Select(attrs={
                'class': 'form-control'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-control'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'transaction_reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Transaction ID / Check number (optional)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Payment notes (optional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show invoices that are not paid or cancelled
        self.fields['invoice'].queryset = Invoice.objects.filter(
            is_active=True,
            status__in=['issued', 'sent', 'viewed', 'overdue']
        ).select_related('client')
    
    def clean_amount(self):
        """Validate payment amount is positive."""
        amount = self.cleaned_data.get('amount', 0)
        if amount <= 0:
            raise forms.ValidationError('Payment amount must be greater than 0.')
        return amount
    
    def clean(self):
        """Validate payment amount against invoice."""
        cleaned_data = super().clean()
        invoice = cleaned_data.get('invoice')
        amount = cleaned_data.get('amount')
        
        if invoice and amount:
            if amount > invoice.amount_due:
                raise forms.ValidationError(
                    f'Payment amount cannot exceed outstanding balance of ${invoice.amount_due:.2f}'
                )
        return cleaned_data
