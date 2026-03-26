"""
Management command to set Kenya-specific default terms and conditions
"""
from django.core.management.base import BaseCommand
from invoicing_app.core.models import CompanySettings


class Command(BaseCommand):
    help = 'Set default terms and conditions for Kenya'

    def handle(self, *args, **options):
        settings = CompanySettings.get_settings()
        
        self.stdout.write("Setting default terms and conditions for Kenya...")
        
        old_terms = settings.terms_and_conditions
        if old_terms and old_terms.strip():
            self.stdout.write(f"\nPrevious terms and conditions:")
            self.stdout.write(f"{old_terms[:150]}...\n")
        
        # Set Kenya-appropriate default terms and conditions
        default_terms = """1. Payment Terms: Net 14 days from invoice date
2. Prices in KES exclude VAT unless otherwise stated
3. Goods/services are provided as specified in invoice
4. Disputes must be raised within 7 days of invoice
5. All work is subject to our standard terms of engagement
6. Late payment charges may apply as per Kenyan law
7. This invoice is valid for payment within 30 days"""
        
        settings.terms_and_conditions = default_terms
        settings.save()
        
        self.stdout.write("\nNew default terms and conditions:")
        self.stdout.write(settings.terms_and_conditions)
        self.stdout.write(self.style.SUCCESS('\nSuccess! Default terms and conditions set for Kenya.'))
