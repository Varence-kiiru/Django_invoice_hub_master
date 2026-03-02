"""Forms for Payment management."""
from django import forms
from .models import Payment, PaymentMethod, PaymentReconciliation
from invoicing_app.invoices.models import Invoice


class PaymentMethodForm(forms.ModelForm):
    """Form for creating and editing payment methods."""
    
    class Meta:
        model = PaymentMethod
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Payment method name (e.g., Bank Transfer, Cash)',
                'maxlength': '100'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Payment method description (optional)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean_name(self):
        """Validate payment method name."""
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Payment method name is required.')
        
        qs = PaymentMethod.objects.filter(name=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('A payment method with this name already exists.')
        return name


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
                'class': 'form-control',
                'id': 'id_invoice'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'min': '0.01'
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
                'placeholder': 'Transaction ID / Check number (optional)',
                'maxlength': '100'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Payment notes (optional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        invoice = kwargs.pop('invoice', None)
        super().__init__(*args, **kwargs)
        
        # Only show unpaid invoices
        self.fields['invoice'].queryset = Invoice.objects.filter(
            is_active=True,
            status__in=['issued', 'sent', 'viewed', 'overdue']
        ).select_related('client').order_by('-invoice_date')
        
        # Pre-select invoice if provided
        if invoice:
            self.fields['invoice'].initial = invoice
        
        # Only show active payment methods
        self.fields['payment_method'].queryset = PaymentMethod.objects.filter(is_active=True)
    
    def clean_amount(self):
        """Validate payment amount is positive."""
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError('Payment amount must be greater than 0.')
        return amount
    
    def clean(self):
        """Validate payment amount against invoice."""
        cleaned_data = super().clean()
        invoice = cleaned_data.get('invoice')
        amount = cleaned_data.get('amount')
        payment_date = cleaned_data.get('payment_date')
        
        if invoice and amount:
            if amount > invoice.amount_due:
                raise forms.ValidationError(
                    f'Payment amount cannot exceed outstanding balance of {invoice.currency} {invoice.amount_due:.2f}'
                )
        
        # Validate payment date is not in the future
        from django.utils import timezone
        if payment_date and payment_date > timezone.now().date():
            raise forms.ValidationError('Payment date cannot be in the future.')
        
        return cleaned_data


class PaymentEditForm(forms.ModelForm):
    """Form for editing payments (only non-sensitive fields)."""
    
    class Meta:
        model = Payment
        fields = ['payment_date', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Payment notes'
            }),
        }
    
    def clean_payment_date(self):
        """Validate payment date is not in the future."""
        from django.utils import timezone
        payment_date = self.cleaned_data.get('payment_date')
        if payment_date and payment_date > timezone.now().date():
            raise forms.ValidationError('Payment date cannot be in the future.')
        return payment_date


class PaymentReconciliationForm(forms.ModelForm):
    """Form for payment reconciliation."""
    
    class Meta:
        model = PaymentReconciliation
        fields = ['amount_matched', 'notes']
        widgets = {
            'amount_matched': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Reconciliation notes (discrepancies, missing items, etc.)'
            }),
        }
    
    def clean_amount_matched(self):
        """Validate matched amount."""
        amount = self.cleaned_data.get('amount_matched')
        if amount is not None and amount < 0:
            raise forms.ValidationError('Matched amount cannot be negative.')
        return amount
