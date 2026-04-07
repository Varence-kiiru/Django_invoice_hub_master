"""
Management command to optimize CompanySettings for Kenya
Sets timezone, date format, currency symbol to Kenya defaults
"""

from django.core.management.base import BaseCommand
from invoicing_app.core.models import CompanySettings


class Command(BaseCommand):
    help = "Optimize CompanySettings for Kenya (timezone, date format, currency)"

    def handle(self, *args, **options):
        settings = CompanySettings.get_settings()

        self.stdout.write("Optimizing CompanySettings for Kenya...")
        self.stdout.write("\nCurrent values:")
        self.stdout.write(f"  Timezone: {settings.timezone}")
        self.stdout.write(f"  Date Format: {settings.date_format}")
        self.stdout.write(f"  Currency Symbol: {settings.currency_symbol}")

        # Update to Kenya defaults
        settings.timezone = "Africa/Nairobi"
        settings.date_format = "DD/MM/YYYY"
        settings.currency_symbol = "KES"
        settings.save()

        self.stdout.write("\nUpdated values:")
        self.stdout.write(f"  Timezone: {settings.timezone}")
        self.stdout.write(f"  Date Format: {settings.date_format}")
        self.stdout.write(f"  Currency Symbol: {settings.currency_symbol}")

        self.stdout.write(
            self.style.SUCCESS("\nSuccess! CompanySettings optimized for Kenya.")
        )
