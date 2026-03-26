"""
Forms for user registration and organization setup.
"""
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re


class SignupForm(forms.Form):
    """
    User registration form with organization creation.
    Handles both user account creation and organization setup.
    """
    
    # User Information
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'your@email.com',
            'autocomplete': 'email',
            'required': True
        }),
        help_text="We'll use this for login and billing notifications"
    )
    
    first_name = forms.CharField(
        label="First Name",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'John',
            'autocomplete': 'given-name'
        })
    )
    
    last_name = forms.CharField(
        label="Last Name",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Doe',
            'autocomplete': 'family-name'
        })
    )
    
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Create a strong password',
            'autocomplete': 'new-password',
            'minlength': '8'
        }),
        help_text="At least 8 characters with uppercase, lowercase, and numbers",
        min_length=8
    )
    
    password_confirm = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password'
        })
    )
    
    # Organization Information
    company_name = forms.CharField(
        label="Company Name",
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Your Company Inc',
            'autocomplete': 'organization'
        }),
        help_text="Your business name or operating as"
    )
    
    company_website = forms.URLField(
        label="Company Website",
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://yourcompany.com',
            'autocomplete': 'url'
        }),
        help_text="Optional: your company website"
    )
    
    # Plan Selection
    PLAN_CHOICES = [
        ('free', 'Free Plan - Start with 50 invoices/month'),
        ('starter', 'Starter Plan - KES 2,999/month for 1000 invoices + team'),
    ]
    
    plan = forms.ChoiceField(
        label="Select Your Plan",
        choices=PLAN_CHOICES,
        initial='free',
        widget=forms.RadioSelect(attrs={
            'class': 'plan-radio',
        }),
        help_text="You can upgrade anytime"
    )
    
    # Terms & Privacy
    agree_terms = forms.BooleanField(
        label="I agree to the Terms of Service and Privacy Policy",
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'required': True
        })
    )
    
    subscribe_newsletter = forms.BooleanField(
        label="Send me tips and product updates",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_email(self):
        """Validate email is unique"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(
                "This email is already registered. Please log in or use a different email.",
                code='email_exists'
            )
        return email
    
    def clean_password(self):
        """Validate password strength"""
        password = self.cleaned_data.get('password')
        
        if len(password) < 8:
            raise ValidationError(
                "Password must be at least 8 characters long.",
                code='password_too_short'
            )
        
        # Check for uppercase
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                "Password must contain at least one uppercase letter.",
                code='password_no_upper'
            )
        
        # Check for lowercase
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                "Password must contain at least one lowercase letter.",
                code='password_no_lower'
            )
        
        # Check for numbers
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                "Password must contain at least one number.",
                code='password_no_number'
            )
        
        return password
    
    def clean(self):
        """Validate password confirmation"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise ValidationError(
                "Passwords do not match. Please enter the same password twice.",
                code='passwords_dont_match'
            )
        
        if not cleaned_data.get('agree_terms'):
            raise ValidationError(
                "You must agree to the Terms of Service to continue.",
                code='must_agree_terms'
            )
        
        return cleaned_data


class CompanySetupForm(forms.Form):
    """
    Post-signup company setup form.
    Collects additional company information for invoicing.
    """
    
    company_name = forms.CharField(
        label="Company Name",
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Your Company Inc'
        })
    )
    
    company_phone = forms.CharField(
        label="Company Phone",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+254 (20) 1234 5678',
            'type': 'tel'
        })
    )
    
    company_website = forms.URLField(
        label="Company Website",
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://yourcompany.com',
            'autocomplete': 'url'
        }),
        help_text="Optional: your company website"
    )
    
    company_email = forms.EmailField(
        label="Company Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'info@yourcompany.com'
        })
    )
    
    company_address = forms.CharField(
        label="Street Address",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123 Main Street'
        })
    )
    
    company_city = forms.CharField(
        label="City",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'New York'
        })
    )
    
    company_state = forms.CharField(
        label="State/Province",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'NY'
        })
    )
    
    company_postal_code = forms.CharField(
        label="ZIP/Postal Code",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '00100'
        })
    )
    
    company_country = forms.CharField(
        label="Country",
        max_length=100,
        initial='Kenya',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Kenya'
        })
    )
    
    company_tax_id = forms.CharField(
        label="Tax ID/VAT Number",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'XX-XXXXXXXXX'
        }),
        help_text="Optional: Your tax ID or VAT number for invoices"
    )
    
    company_industry = forms.CharField(
        label="Industry",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Software/Services/Retail/Other'
        })
    )
    
    company_registration_number = forms.CharField(
        label="Company Registration Number",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 123456789'
        }),
        help_text="Optional: Your company's official registration number"
    )


class LoginForm(forms.Form):
    """
    User login form.
    """
    
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'your@email.com',
            'autocomplete': 'email'
        })
    )
    
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })
    )
    
    remember_me = forms.BooleanField(
        label="Remember me for 30 days",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
