"""
Security middleware and utilities for production deployment.
Includes rate limiting, security headers, and CORS configuration.
"""

from django.http import HttpResponse
from django.core.cache import cache
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Simple rate limiting middleware using Django cache.
    Tracks requests per IP and enforces limits.
    """

    # Rate limit config: (requests, time_window_seconds)
    RATE_LIMITS = {
        "default": (100, 3600),  # 100 requests per hour
        "signup": (
            20,
            3600,
        ),  # 20 requests per hour for signup (more lenient - form reloads)
        "login": (5, 300),  # 5 attempts per 5 minutes for login (strict - brute force)
        "api": (1000, 3600),  # 1000 requests per hour for API
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get client IP
        client_ip = self._get_client_ip(request)

        # Check rate limit
        if not self._check_rate_limit(request, client_ip):
            return HttpResponse(
                "Too many requests. Please try again later.", status=429
            )

        response = self.get_response(request)
        return response

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def _check_rate_limit(self, request, client_ip):
        """Check if client has exceeded rate limit"""
        # Determine rate limit category
        if "api" in request.path:
            category = "api"
        elif "signup" in request.path or "register" in request.path:
            category = "signup"
        elif "login" in request.path or "token" in request.path:
            category = "login"
        else:
            category = "default"

        limit, window = self.RATE_LIMITS.get(category, self.RATE_LIMITS["default"])

        # Create cache key
        cache_key = f"rate_limit:{category}:{client_ip}"

        # Get current request count
        current = cache.get(cache_key, 0)

        if current >= limit:
            logger.warning(
                f"Rate limit exceeded for {client_ip} (category: {category})"
            )
            return False

        # Increment request count
        cache.set(cache_key, current + 1, window)
        return True


def rate_limit(category="default"):
    """
    Decorator to apply rate limiting to specific views.

    Usage:
        @rate_limit('auth')
        def login_view(request):
            ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            client_ip = RateLimitMiddleware._get_client_ip(request)
            limits = RateLimitMiddleware.RATE_LIMITS
            limit, window = limits.get(category, limits["default"])

            cache_key = f"rate_limit:{category}:{client_ip}"
            current = cache.get(cache_key, 0)

            if current >= limit:
                return HttpResponse(
                    "Too many requests. Please try again later.", status=429
                )

            cache.set(cache_key, current + 1, window)
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


class SecurityHeadersMiddleware:
    """
    Add security headers to all responses.
    """

    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Add security headers
        for header, value in self.SECURITY_HEADERS.items():
            response[header] = value

        return response


class CSPMiddleware:
    """
    Content Security Policy (CSP) middleware.
    Prevents XSS, inline script injection, and
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Build CSP header
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.jsdelivr.net cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com fonts.googleapis.com; "
            "font-src 'self' fonts.gstatic.com cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.stripe.com; "
            "frame-src 'self' https://js.stripe.com; "
        )

        response["Content-Security-Policy"] = csp_policy
        return response


class CORSConfig:
    """
    CORS configuration for API access.
    """

    @staticmethod
    def get_allowed_origins():
        """Get list of allowed CORS origins"""
        from django.conf import settings

        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:8000",
            "http://localhost:8001",
        ]

        if hasattr(settings, "ALLOWED_ORIGINS"):
            allowed_origins.extend(settings.ALLOWED_ORIGINS)

        return allowed_origins

    @staticmethod
    def get_cors_config():
        """Get complete CORS configuration"""
        return {
            "CORS_ALLOWED_ORIGINS": CORSConfig.get_allowed_origins(),
            "CORS_ALLOW_CREDENTIALS": True,
            "CORS_ALLOW_METHODS": [
                "DELETE",
                "GET",
                "OPTIONS",
                "PATCH",
                "POST",
                "PUT",
            ],
            "CORS_ALLOW_HEADERS": [
                "accept",
                "accept-encoding",
                "authorization",
                "content-type",
                "dnt",
                "origin",
                "user-agent",
                "x-csrftoken",
                "x-requested-with",
            ],
        }


class InputValidator:
    """
    Input validation utilities to prevent SQL injection and XSS.
    """

    DANGEROUS_STRINGS = [
        "DROP",
        "DELETE",
        "INSERT",
        "UPDATE",
        "SELECT",
        "<script>",
        "</script>",
        "javascript:",
        "onerror=",
        "onload=",
        "alert(",
        "document.",
        "window.",
    ]

    @staticmethod
    def is_safe_string(s):
        """Check if string is safe from injection attacks"""
        if not isinstance(s, str):
            return True

        s_upper = s.upper()
        for dangerous in InputValidator.DANGEROUS_STRINGS:
            if dangerous in s_upper:
                return False

        return True

    @staticmethod
    def sanitize_input(data):
        """Sanitize user input"""
        from django.utils.html import escape

        if isinstance(data, str):
            return escape(data)
        elif isinstance(data, dict):
            return {k: InputValidator.sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [InputValidator.sanitize_input(item) for item in data]

        return data


def validate_organization_access(view_func):
    """
    Decorator to validate that user has access to requested organization.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from .models import OrganizationMember

        org_slug = kwargs.get("slug") or request.GET.get("org")

        if org_slug:
            try:
                member = OrganizationMember.objects.get(
                    user=request.user, organization__slug=org_slug, is_active=True
                )
                request.current_organization = member.organization
                request.current_member = member
            except OrganizationMember.DoesNotExist:
                return HttpResponse("Access denied", status=403)

        return view_func(request, *args, **kwargs)

    return wrapper
