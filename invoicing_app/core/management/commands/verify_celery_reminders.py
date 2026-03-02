"""
Management command to verify Celery tasks and send test notifications.
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Verify Celery task configuration and send test tasks."""
    
    help = 'Verify Celery tasks and email reminder system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Send test tasks to Celery queue',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List registered Celery tasks',
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show Celery worker and broker status',
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        from invoicing_app.celery import app
        
        if options['list']:
            self.list_tasks(app)
        elif options['status']:
            self.check_status(app)
        elif options['test']:
            self.test_tasks(app)
        else:
            self.verify_config()
    
    def list_tasks(self, app):
        """List all registered Celery tasks."""
        self.stdout.write(self.style.SUCCESS('\n=== Registered Celery Tasks ===\n'))
        
        for task_name in sorted(app.tasks.keys()):
            if not task_name.startswith('celery.'):  # Skip internal Celery tasks
                self.stdout.write(f'  ✓ {task_name}')
        
        self.stdout.write(self.style.SUCCESS('\n=== Beat Schedule ===\n'))
        
        for schedule_name, config in app.conf.beat_schedule.items():
            task = config.get('task', 'unknown')
            schedule = config.get('schedule', 'unknown')
            self.stdout.write(f'  {schedule_name}:')
            self.stdout.write(f'    Task: {task}')
            self.stdout.write(f'    Schedule: {schedule}\n')
    
    def check_status(self, app):
        """Check Celery broker and worker status."""
        self.stdout.write(self.style.SUCCESS('\n=== Celery Status ===\n'))
        
        # Check broker connection
        try:
            with app.connection() as conn:
                conn.connect()
            self.stdout.write(self.style.SUCCESS(f'✓ Broker connected: {app.conf.broker_url}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Broker error: {str(e)}'))
        
        # Check registered tasks
        registered_tasks = len([t for t in app.tasks.keys() if not t.startswith('celery.')])
        self.stdout.write(f'✓ Registered tasks: {registered_tasks}')
        
        # Check Beat schedule
        beat_tasks = len(app.conf.beat_schedule)
        self.stdout.write(f'✓ Scheduled tasks: {beat_tasks}')
        
        self.stdout.write(self.style.SUCCESS('\nDebug Tip: Run the following to start Celery worker and beat:'))
        self.stdout.write(self.style.WARNING('  celery -A invoicing_app worker -l info'))
        self.stdout.write(self.style.WARNING('  celery -A invoicing_app beat -l info'))
    
    def test_tasks(self, app):
        """Send test tasks to Celery queue."""
        from invoicing_app.notifications.tasks import (
            send_invoice_reminders,
            send_payment_reminders,
            cleanup_old_notification_logs,
        )
        
        self.stdout.write(self.style.SUCCESS('\n=== Sending Test Tasks ===\n'))
        
        try:
            # Test 1: Send invoice reminders
            task1 = send_invoice_reminders.delay()
            self.stdout.write(f'✓ send_invoice_reminders sent (Task ID: {task1.id})')
            
            # Test 2: Send payment reminders
            task2 = send_payment_reminders.delay()
            self.stdout.write(f'✓ send_payment_reminders sent (Task ID: {task2.id})')
            
            # Test 3: Cleanup old logs
            task3 = cleanup_old_notification_logs.delay()
            self.stdout.write(f'✓ cleanup_old_notification_logs sent (Task ID: {task3.id})')
            
            self.stdout.write(self.style.SUCCESS('\nTest tasks sent! Check Celery worker logs for execution.'))
            self.stdout.write(self.style.WARNING('Note: Make sure Celery worker is running: celery -A invoicing_app worker -l info'))
            
        except Exception as e:
            raise CommandError(f'Error sending test tasks: {str(e)}')
    
    def verify_config(self):
        """Verify basic configuration."""
        self.stdout.write(self.style.SUCCESS('\n=== Email Reminder System Verification ===\n'))
        
        from invoicing_app.celery import app
        from invoicing_app.core.models import CompanySettings
        
        # 1. Check company settings
        try:
            settings = CompanySettings.get_settings()
            enabled = '✓ Enabled' if settings.enable_reminders else '✗ Disabled'
            self.stdout.write(f'Reminders status: {enabled}')
            self.stdout.write(f'Company: {settings.company_name}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading settings: {str(e)}'))
        
        # 2. Check email configuration
        try:
            from invoicing_app.core.models import EmailConfiguration
            email_config = EmailConfiguration.get_settings()
            self.stdout.write(f'Email backend: {email_config.backend}')
            self.stdout.write(f'Email host: {email_config.host}')
            if email_config.host:
                self.stdout.write(self.style.SUCCESS('✓ Email configured'))
            else:
                self.stdout.write(self.style.WARNING('⚠ Email not configured'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Email config not set: {str(e)}'))
        
        # 3. Check Celery configuration
        self.stdout.write(f'\nCelery Broker: {app.conf.broker_url}')
        self.stdout.write(f'Result Backend: {app.conf.result_backend}')
        
        # 4. Check Beat schedule
        self.stdout.write(f'\nBeat scheduled tasks:')
        for schedule_name in app.conf.beat_schedule.keys():
            self.stdout.write(f'  ✓ {schedule_name}')
        
        self.stdout.write(self.style.SUCCESS('\n✓ Configuration verified!\n'))
        
        # Show next steps
        self.stdout.write(self.style.WARNING('Next Steps:'))
        self.stdout.write('1. Start Celery worker: celery -A invoicing_app worker -l info')
        self.stdout.write('2. Start Celery beat: celery -A invoicing_app beat -l info')
        self.stdout.write('3. Test tasks: python manage.py verify_celery_reminders --test')
        self.stdout.write('4. Check status: python manage.py verify_celery_reminders --status')
