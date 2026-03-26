"""Forms for deliveries management."""
from django import forms
from invoicing_app.deliveries.models import Delivery


class DeliveryForm(forms.ModelForm):
    """Form for creating and editing deliveries."""
    
    class Meta:
        model = Delivery
        fields = [
            'invoice',
            'scheduled_date',
            'actual_delivery_date',
            'delivery_time',
            'delivery_method',
            'delivery_location',
            'recipient_name',
            'condition',
            'condition_notes',
            'notes',
        ]
        widgets = {
            'invoice': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'scheduled_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True,
            }),
            'actual_delivery_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'delivery_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'delivery_method': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'delivery_location': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Complete delivery address...',
            }),
            'recipient_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Name of person receiving...',
            }),
            'condition': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'condition_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Any notes about item condition...',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any additional notes about this delivery...',
            }),
        }
