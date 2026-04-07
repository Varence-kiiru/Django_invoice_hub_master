"""
Webhook handlers for payment processing events.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import stripe
import logging
from .stripe_integration import SubscriptionManager

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Handle Stripe webhook events.

    Events handled:
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_succeeded
    - invoice.payment_failed
    - charge.dispute.created
    """
    from django.conf import settings

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Invalid payload in Stripe webhook")
        return JsonResponse({"error": "Invalid payload"}, status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature in Stripe webhook")
        return JsonResponse({"error": "Invalid signature"}, status=403)

    try:
        # Handle the event
        SubscriptionManager.handle_webhook(event)
        return JsonResponse({"status": "success"})
    except Exception as e:
        logger.error(f"Error processing webhook {event['type']}: {str(e)}")
        return JsonResponse({"error": "Internal error"}, status=500)
