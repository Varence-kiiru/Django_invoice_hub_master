"""
Management command to test email reminders manually.

Usage:
    python manage.py test_reminders --type=invoice
    python manage.py test_reminders --type=payment
    python manage.py test_reminders --type=all

This command allows you to test the reminder system without waiting for scheduled tasks.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from invoicing_app.notifications.tasks import (
    send_invoice_reminders,
    send_payment_reminders,
)
from invoicing_app.invoices.tasks import check_and_update_overdue_invoices
from invoicing_app.core.models import CompanySettings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test email reminders manually (bypass Celery scheduler)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            default='all',
            choices=['all', 'invoice', 'payment', 'overdue'],
            help='Type of reminder to test: all, invoice, payment, or overdue'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force send reminders even if disabled in settings'
        )

    def handle(self, *args, **options):
        reminder_type = options['type']
        force = options['force']

        # Check if reminders are enabled
        settings = CompanySettings.get_settings()
        if not settings.enable_reminders and not force:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  Email reminders are disabled in Company Settings.\n'
                    'Enable them in Settings > Company > Enable Reminders\n'
                    'Or use --force flag to test anyway.'
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS('🚀 Testing Email Reminder System')
        )
        self.stdout.write(f'Time: {timezone.now()}')
        self.stdout.write('─' * 60)

        try:
            if reminder_type in ['all', 'overdue']:
                self.stdout.write('\n📋 Checking for overdue invoices...')
                result = check_and_update_overdue_invoices()
                self._print_result(result, 'Overdue check')

            if reminder_type in ['all', 'invoice']:
                self.stdout.write('\n📧 Sending invoice reminders...')
                result = send_invoice_reminders()
                self._print_result(result, 'Invoice reminders')

            if reminder_type in ['all', 'payment']:
                self.stdout.write('\n💳 Sending payment reminders...')
                result = send_payment_reminders()
                self._print_result(result, 'Payment reminders')

            self.stdout.write('─' * 60)
            self.stdout.write(
                self.style.SUCCESS('✅ Reminder test completed successfully!')
            )
            self.stdout.write('\n📝 Check these locations for verification:')
            self.stdout.write('  1. Admin > Audit > Notification Logs')
            self.stdout.write('  2. Admin > Invoices > Invoice (view history)')
            self.stdout.write('  3. Email inbox (if email is configured)')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error testing reminders: {str(e)}')
            )
            logger.exception('Error in test_reminders command')
            raise CommandError(f'Failed to test reminders: {str(e)}')

    def _print_result(self, result, label):
        """Pretty-print task result."""
        status = result.get('status', 'unknown')
        sent = result.get('sent', 0)
        updated = result.get('updated', 0)
        deleted = result.get('deleted', 0)
        error = result.get('error')

        if status == 'success':
            if sent > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ {label}: Sent {sent} reminders')
                )
            elif updated > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ {label}: Updated {updated} invoices')
                )
            elif deleted > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ {label}: Cleaned up {deleted} logs')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✅ {label}: No action needed (all invoices current)'
                    )
                )
        elif status == 'disabled':
            self.stdout.write(
                self.style.WARNING(f'  ⚠️  {label}: Disabled in settings')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'  ❌ {label}: {error or status}')
            )
