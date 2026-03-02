"""Forms for Product management."""
from django import forms
from .models import Product, ProductCategory, ProductTaxClass


class ProductCategoryForm(forms.ModelForm):
    """Form for creating and editing product categories."""
    
    class Meta:
        model = ProductCategory
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name (e.g., Software, Services)',
                'maxlength': '100'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Category description'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean_name(self):
        """Validate category name."""
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Category name is required.')
        # Check uniqueness
        qs = ProductCategory.objects.filter(name=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('A category with this name already exists.')
        return name


class ProductTaxClassForm(forms.ModelForm):
    """Form for creating and editing tax classes."""
    
    class Meta:
        model = ProductTaxClass
        fields = ['name', 'rate_type']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tax class name (e.g., Standard VAT)',
                'maxlength': '100'
            }),
            'rate_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_rate_type'
            }),
        }
    
    def clean_name(self):
        """Validate tax class name."""
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Tax class name is required.')
        # Check uniqueness
        qs = ProductTaxClass.objects.filter(name=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('A tax class with this name already exists.')
        return name


class ProductForm(forms.ModelForm):
    """Form for creating and editing products."""
    
    class Meta:
        model = Product
        fields = [
            'sku', 'name', 'description', 'unit_price', 'unit',
            'category', 'tax_class'
        ]
        widgets = {
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Product SKU'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Product name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Product description'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'unit': forms.Select(attrs={
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'tax_class': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def clean_sku(self):
        """Validate SKU uniqueness."""
        sku = self.cleaned_data.get('sku', '').strip()
        if sku:
            qs = Product.objects.filter(sku=sku)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('A product with this SKU already exists.')
        return sku
    
    def clean_unit_price(self):
        """Validate unit price."""
        price = self.cleaned_data.get('unit_price', 0)
        if price < 0:
            raise forms.ValidationError('Unit price cannot be negative.')
        return price
    
    def clean_name(self):
        """Validate product name."""
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Product name is required.')
        return name
