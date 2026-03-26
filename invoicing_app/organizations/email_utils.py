"""Email utilities for organization authentication and verification."""
import os
import hashlib
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.timezone import now
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def generate_verification_token(user_id, email):
    """
    Generate a verification token for email verification.
    Uses user ID and email hash for simplicity.
    """
    secret = f"{user_id}:{email}:{settings.SECRET_KEY}"
    token = hashlib.sha256(secret.encode()).hexdigest()
    return token


def send_verification_email(request, user, organization):
    """
    Send verification email to user after signup.
    """
    try:
        token = generate_verification_token(user.id, user.email)
        
        # Build verification URL
        verification_url = request.build_absolute_uri(
            reverse('organizations:email_verification', kwargs={'token': token})
        )
        
        # Render email template
        html_message = render_to_string('emails/verify_email.html', {
            'user': user,
            'organization': organization,
            'verification_url': verification_url,
            'token': token,
        })
        
        # Send email
        send_mail(
            subject=f'Verify your email for {organization.name}',
            message=f'Please verify your email by visiting: {verification_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Verification email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        return False


def send_welcome_email(request, user, organization):
    """
    Send welcome email after successful signup.
    """
    try:
        html_message = render_to_string('emails/welcome_email.html', {
            'user': user,
            'organization': organization,
            'dashboard_url': request.build_absolute_uri(reverse('core:dashboard')),
        })
        
        send_mail(
            subject=f'Welcome to {organization.name}!',
            message=f'Welcome to {organization.name}! You can now start creating invoices.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Welcome email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False


def send_subscription_upgrade_email(user, organization, new_plan):
    """
    Send email when subscription is upgraded.
    """
    try:
        html_message = render_to_string('emails/subscription_upgrade.html', {
            'user': user,
            'organization': organization,
            'new_plan': new_plan,
        })
        
        send_mail(
            subject=f'Your plan has been upgraded to {new_plan.title()}',
            message=f'Your subscription has been upgraded to {new_plan}.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Upgrade email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send upgrade email to {user.email}: {str(e)}")
        return False
