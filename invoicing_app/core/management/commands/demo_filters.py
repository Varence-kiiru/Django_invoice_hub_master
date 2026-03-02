"""
Management command to test and demonstrate advanced search & filtering.

Usage:
    python manage.py demo_filters --type=invoice --help
    python manage.py demo_filters --type=invoice --filter='{"status": ["unpaid", "overdue"]}'
"""

from django.core.management.base import BaseCommand
from invoicing_app.invoices.models import Invoice
from invoicing_app.payments.models import Payment
from invoicing_app.clients.models import Client
from invoicing_app.quotations.models import Quote
from invoicing_app.core.search_filters import (
    AdvancedFilterBuilder, FullTextSearch, FilterPreset, get_filter_options
)
import json


class Command(BaseCommand):
    help = 'Demo advanced filtering and search capabilities'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['invoice', 'payment', 'client', 'quotation'],
            default='invoice',
            help='Type of entity to filter'
        )
        parser.add_argument(
            '--filter',
            type=str,
            help='JSON filter criteria (e.g., \'{"status": "unpaid"}\')'
        )
        parser.add_argument(
            '--search',
            type=str,
            help='Full-text search query'
        )
        parser.add_argument(
            '--show-options',
            action='store_true',
            help='Show available filter options'
        )

    def handle(self, *args, **options):
        entity_type = options['type']
        filter_json = options.get('filter')
        search_query = options.get('search')
        show_options = options.get('show_options', False)

        self.stdout.write(
            self.style.SUCCESS('🔍 Advanced Search & Filtering Demo')
        )
        self.stdout.write('─' * 70)

        # Show available options
        if show_options:
            self._show_filter_options(entity_type)
            return

        # Parse filter criteria
        criteria = {}
        if filter_json:
            try:
                criteria = json.loads(filter_json)
                self.stdout.write(self.style.SUCCESS(f'✓ Filter: {criteria}'))
            except json.JSONDecodeError as e:
                self.stdout.write(self.style.ERROR(f'✗ Invalid JSON: {str(e)}'))
                return

        # Get queryset
        if entity_type == 'invoice':
            queryset = Invoice.objects.all().select_related('client')
        elif entity_type == 'payment':
            queryset = Payment.objects.all().select_related('invoice')
        elif entity_type == 'quotation':
            queryset = Quote.objects.all().select_related('client')
        else:  # client
            queryset = Client.objects.all()

        # Apply filters
        if criteria:
            queryset = self._apply_filters(entity_type, queryset, criteria)
            self.stdout.write(f'After filter: {queryset.count()} results')

        # Apply search
        if search_query:
            queryset = self._apply_search(entity_type, queryset, search_query)
            self.stdout.write(f'After search: {queryset.count()} results')

        self.stdout.write('─' * 70)

        # Display results
        self._display_results(entity_type, queryset[:5])

    def _show_filter_options(self, entity_type):
        """Display available filter options."""
        options = get_filter_options(entity_type)
        
        self.stdout.write(f'\n📋 Available Filters for {entity_type.upper()}:')
        self.stdout.write('─' * 70)
        
        if 'statuses' in options:
            self.stdout.write('\nStatus options:')
            for status in options['statuses']:
                self.stdout.write(f'  • {status}')
        
        if 'methods' in options:
            self.stdout.write('\nPayment methods:')
            for method in options['methods']:
                self.stdout.write(f'  • {method}')
        
        if 'types' in options:
            self.stdout.write('\nTypes:')
            for t in options['types']:
                self.stdout.write(f'  • {t}')
        
        if 'date_ranges' in options:
            self.stdout.write('\nDate ranges:')
            for date_range in options['date_ranges']:
                self.stdout.write(f'  • {date_range}')
        
        self.stdout.write('\n📝 Example filters:')
        self.stdout.write(f'  python manage.py demo_filters --type={entity_type} --filter=\'{{\"status\": \"draft\"}}\'')
        self.stdout.write(f'  python manage.py demo_filters --type={entity_type} --search="client name"')

    def _apply_filters(self, entity_type, queryset, criteria):
        """Apply filters to queryset."""
        if entity_type == 'invoice':
            return AdvancedFilterBuilder.apply_invoice_filters(queryset, criteria)
        elif entity_type == 'payment':
            return AdvancedFilterBuilder.apply_payment_filters(queryset, criteria)
        elif entity_type == 'quotation':
            return AdvancedFilterBuilder.apply_quotation_filters(queryset, criteria)
        else:  # client
            return AdvancedFilterBuilder.apply_client_filters(queryset, criteria)

    def _apply_search(self, entity_type, queryset, search_query):
        """Apply full-text search to queryset."""
        if entity_type == 'invoice':
            return FullTextSearch.search_invoices(queryset, search_query)
        elif entity_type == 'payment':
            return FullTextSearch.search_payments(queryset, search_query)
        elif entity_type == 'quotation':
            return FullTextSearch.search_quotations(queryset, search_query)
        else:  # client
            return FullTextSearch.search_clients(queryset, search_query)

    def _display_results(self, entity_type, queryset):
        """Display filtered results."""
        if not queryset:
            self.stdout.write(self.style.WARNING('No results found'))
            return

        self.stdout.write(f'\n📊 Displaying {min(5, queryset.count())} of {queryset.count()} results:\n')

        if entity_type == 'invoice':
            for inv in queryset:
                self.stdout.write(
                    f'  • {inv.invoice_number} | {inv.client.name} | '
                    f'{inv.total_amount} {inv.currency} | {inv.status}'
                )
        elif entity_type == 'payment':
            for pmt in queryset:
                invoice_num = pmt.invoice.invoice_number if pmt.invoice else 'N/A'
                self.stdout.write(
                    f'  • {pmt.receipt_number} | Inv#{invoice_num} | '
                    f'{pmt.amount} {pmt.currency} | {pmt.status}'
                )
        elif entity_type == 'quotation':
            for quote in queryset:
                self.stdout.write(
                    f'  • {quote.quote_number} | {quote.client.name} | '
                    f'{quote.total_amount} {quote.currency} | {quote.status}'
                )
        else:  # client
            for client in queryset:
                self.stdout.write(
                    f'  • {client.name} | {client.email} | {client.client_type}'
                )
