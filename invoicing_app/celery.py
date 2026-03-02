"""
Celery configuration and application instance.

This module sets up Celery with Django for async task management.
- Redis as message broker
- Redis as result backend
- Celery Beat for scheduled tasks
"""

import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'invoicing_app.settings.development')

# Create Celery app
app = Celery('invoicing_app')

# Load configuration from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
# This defines when scheduled tasks should run
app.conf.beat_schedule = {
    # Send invoice reminders every day at 9 AM
    'send-invoice-reminders': {
        'task': 'invoicing_app.notifications.tasks.send_invoice_reminders',
        'schedule': crontab(hour=9, minute=0),
        'options': {'queue': 'default'}
    },
    # Check for overdue invoices every hour
    'check-overdue-invoices': {
        'task': 'invoicing_app.invoices.tasks.check_and_update_overdue_invoices',
        'schedule': crontab(minute=0),  # Every hour
        'options': {'queue': 'default'}
    },
    # Send payment reminders for invoices due tomorrow
    'send-payment-reminders': {
        'task': 'invoicing_app.notifications.tasks.send_payment_reminders',
        'schedule': crontab(hour=14, minute=0),  # 2 PM daily
        'options': {'queue': 'default'}
    },
    # Clean up old notification logs (weekly, Sunday at midnight)
    'cleanup-old-notifications': {
        'task': 'invoicing_app.notifications.tasks.cleanup_old_notification_logs',
        'schedule': crontab(day_of_week=0, hour=0, minute=0),
        'options': {'queue': 'default'}
    },
}

# Task routing (optional: route certain tasks to specific queues)
app.conf.task_routes = {
    'invoicing_app.notifications.tasks.*': {'queue': 'notifications'},
    'invoicing_app.invoices.tasks.*': {'queue': 'invoices'},
}

# Task configuration
app.conf.update(
    # Task time limits (prevent hanging tasks)
    task_soft_time_limit=300,  # 5 minutes soft limit (task receives signal)
    task_time_limit=600,  # 10 minutes hard limit (task killed)
    
    # Task acknowledgment (process only after completion)
    task_acks_late=True,
    
    # Worker configuration
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f'Request: {self.request!r}')
