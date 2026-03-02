"""
Forms for tax rate management.
"""
from django import forms
from .models import TaxRate, VATRule


class TaxRateForm(forms.ModelForm):
    """Form for creating and editing tax rates."""
    
    class Meta:
        model = TaxRate
        fields = [
            'code', 'name', 'rate_percentage', 'tax_type', 
            'country', 'effective_from', 'effective_to',
            'is_vat_applicable', 'kra_code', 'description'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., VAT16, VAT0',
                'maxlength': '20'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Standard VAT (16%)',
                'maxlength': '100'
            }),
            'rate_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '16.00',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'tax_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Kenya',
                'maxlength': '100'
            }),
            'effective_from': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'effective_to': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': False
            }),
            'is_vat_applicable': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'kra_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(Optional)',
                'maxlength': '50'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description for reference'
            }),
        }
    
    def clean(self):
        """Validate tax rate form."""
        super().clean()
        code = self.cleaned_data.get('code', '').strip().upper()
        rate_percentage = self.cleaned_data.get('rate_percentage')
        effective_from = self.cleaned_data.get('effective_from')
        effective_to = self.cleaned_data.get('effective_to')
        
        # Validate rate percentage
        if rate_percentage is not None:
            if rate_percentage < 0 or rate_percentage > 100:
                self.add_error('rate_percentage', 'Rate must be between 0 and 100')
        
        # Validate effective dates
        if effective_from and effective_to:
            if effective_from > effective_to:
                self.add_error('effective_to', 'Effective To must be after Effective From')
        
        # Check code uniqueness
        if code:
            qs = TaxRate.objects.filter(code=code)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('code', 'A tax rate with this code already exists')
        
        return self.cleaned_data
    
    def save(self, commit=True):
        """Save tax rate with uppercase code."""
        instance = super().save(commit=False)
        instance.code = instance.code.upper().strip()
        if commit:
            instance.save()
        return instance


class VATRuleForm(forms.ModelForm):
    """Form for creating and editing VAT rules."""
    
    class Meta:
        model = VATRule
        fields = ['name', 'tax_class', 'tax_rate', 'priority', 'is_active', 'condition']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Export goods - zero-rated',
                'maxlength': '100'
            }),
            'tax_class': forms.Select(attrs={
                'class': 'form-control',
            }),
            'tax_rate': forms.Select(attrs={
                'class': 'form-control',
            }),
            'priority': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '100',
                'min': '0',
                'max': '1000'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'condition': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '(Optional) JSON condition for future use',
            }),
        }
    
    def clean(self):
        """Validate VAT rule form."""
        super().clean()
        return self.cleaned_data



class TaxRateForm(forms.ModelForm):
    """Form for creating and editing tax rates."""
    
    class Meta:
        model = TaxRate
        fields = [
            'code', 'name', 'rate_percentage', 'tax_type', 
            'country', 'effective_from', 'effective_to',
            'is_vat_applicable', 'kra_code', 'description'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., VAT16, VAT0',
                'maxlength': '20'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Standard VAT (16%)',
                'maxlength': '100'
            }),
            'rate_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '16.00',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'tax_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Kenya',
                'maxlength': '100'
            }),
            'effective_from': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'effective_to': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': False
            }),
            'is_vat_applicable': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'kra_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(Optional)',
                'maxlength': '50'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description for reference'
            }),
        }
    
    def clean(self):
        """Validate tax rate form."""
        super().clean()
        code = self.cleaned_data.get('code', '').strip().upper()
        rate_percentage = self.cleaned_data.get('rate_percentage')
        effective_from = self.cleaned_data.get('effective_from')
        effective_to = self.cleaned_data.get('effective_to')
        
        # Validate rate percentage
        if rate_percentage is not None:
            if rate_percentage < 0 or rate_percentage > 100:
                self.add_error('rate_percentage', 'Rate must be between 0 and 100')
        
        # Validate effective dates
        if effective_from and effective_to:
            if effective_from > effective_to:
                self.add_error('effective_to', 'Effective To must be after Effective From')
        
        # Check code uniqueness
        if code:
            qs = TaxRate.objects.filter(code=code)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('code', 'A tax rate with this code already exists')
        
        return self.cleaned_data
    
    def save(self, commit=True):
        """Save tax rate with uppercase code."""
        instance = super().save(commit=False)
        instance.code = instance.code.upper().strip()
        if commit:
            instance.save()
        return instance
