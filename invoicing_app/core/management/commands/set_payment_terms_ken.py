"""
Management command to set Kenya-specific default payment terms
"""
from django.core.management.base import BaseCommand
from invoicing_app.core.models import CompanySettings


class Command(BaseCommand):
    help = 'Set default payment terms for Kenya (Net 14 days)'

    def handle(self, *args, **options):
        settings = CompanySettings.get_settings()
        
        self.stdout.write("Setting default payment terms for Kenya...")
        self.stdout.write(f"\nCurrent payment terms: {settings.default_payment_terms or 'None'}")
        
        # Set Kenya-appropriate payment terms (Net 14 days is common in East Africa)
        settings.default_payment_terms = "Payment due within 14 days of invoice date"
        settings.save()
        
        self.stdout.write(f"New payment terms: {settings.default_payment_terms}")
        self.stdout.write(self.style.SUCCESS('\nSuccess! Default payment terms set to Net 14 days.'))
