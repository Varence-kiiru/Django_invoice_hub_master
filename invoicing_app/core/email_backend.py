"""
Dynamic Email Backend that reads configuration from database at runtime.

This backend allows email settings to be changed without restarting Django.
Falls back to environment variables if database configuration is not available.
"""
import logging
from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class DynamicEmailBackend(EmailBackend):
    """
    Custom email backend that reads SMTP configuration from database at runtime.
    
    Features:
    - Reads EmailConfiguration from database each time (no caching)
    - Falls back to .env configuration if database is unavailable
    - Supports encryption of stored passwords
    - Allows runtime configuration changes without Django restart
    - Handles connection failures gracefully with fallback
    
    Usage:
        Set in Django settings:
        EMAIL_BACKEND = 'invoicing_app.core.email_backend.DynamicEmailBackend'
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        """
        Initialize the backend by reading configuration from database.
        
        Falls back to environment configuration if database is unavailable.
        This allows the system to continue working during migration or database issues.
        """
        self.fail_silently = fail_silently
        
        try:
            # Try to get configuration from database
            from invoicing_app.core.models import EmailConfiguration
            
            # Get or create the singleton configuration
            email_config = EmailConfiguration.get_config()
            
            # Use database configuration
            host = email_config.smtp_host
            port = email_config.smtp_port
            username = email_config.smtp_username
            password = email_config._decrypt_password()
            use_tls = email_config.smtp_use_tls
            use_ssl = email_config.smtp_use_ssl
            
            logger.debug(f"Using email configuration from database: {host}:{port}")
            
        except Exception as e:
            # Fallback to environment variables
            logger.warning(f"Could not load email config from database: {e}. Using environment variables.")
            
            host = settings.EMAIL_HOST
            port = settings.EMAIL_PORT
            username = settings.EMAIL_HOST_USER
            password = settings.EMAIL_HOST_PASSWORD
            use_tls = settings.EMAIL_USE_TLS
            use_ssl = settings.EMAIL_USE_SSL
        
        # Initialize parent EmailBackend with configuration
        super().__init__(
            host=host,
            port=port,
            username=username,
            password=password,
            use_tls=use_tls,
            use_ssl=use_ssl,
            fail_silently=fail_silently,
        )
    
    def send_messages(self, email_messages):
        """
        Send messages using the current database configuration.
        
        Re-initializes configuration each time to allow for runtime changes.
        
        Args:
            email_messages: List of EmailMessage objects to send
        
        Returns:
            Number of successfully sent messages
        """
        if not email_messages:
            return 0
        
        try:
            # Re-check configuration each time to pick up runtime changes
            from invoicing_app.core.models import EmailConfiguration
            email_config = EmailConfiguration.get_config()
            
            # Update connection parameters if configuration changed
            self.host = email_config.smtp_host
            self.port = email_config.smtp_port
            self.username = email_config.smtp_username
            self.password = email_config._decrypt_password()
            self.use_tls = email_config.smtp_use_tls
            self.use_ssl = email_config.smtp_use_ssl
            
            # Reset connection to use new settings
            self.connection = None
            
        except Exception as e:
            logger.warning(f"Could not refresh email config from database: {e}. Using existing settings.")
        
        return super().send_messages(email_messages)
    
    def open(self):
        """
        Create and establish SMTP connection with current configuration.
        
        Overrides parent method to provide better error handling and logging.
        """
        try:
            return super().open()
        except Exception as e:
            error_msg = f"Failed to establish SMTP connection to {self.host}:{self.port}: {str(e)}"
            logger.error(error_msg)
            
            if not self.fail_silently:
                raise
            
            return False
