"""
Billing and subscription management views for organizations.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import logging
from django.utils import timezone

from .models import OrganizationMember, Subscription, Invoice
from .stripe_integration import SubscriptionManager
from django.conf import settings

logger = logging.getLogger(__name__)


def get_user_organization(user):
    """
    Get user's primary organization.
    """
    try:
        # Get primary memberships - there should only be one, but handle multiple gracefully
        primary_memberships = OrganizationMember.objects.filter(
            user=user, is_primary=True
        )

        if not primary_memberships.exists():
            return None

        if primary_memberships.count() > 1:
            # Log warning and return the first one (shouldn't happen in normal operation)
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"User {user.email} has {primary_memberships.count()} primary organization memberships. Using first one."
            )

        member = primary_memberships.first()
        return member.organization
    except Exception:
        return None


@login_required(login_url="organizations:login")
def billing_dashboard_view(request):
    """
    Main billing dashboard showing subscription status and usage.
    """
    organization = get_user_organization(request.user)
    if not organization:
        messages.error(request, "No organization found.")
        return redirect("core:dashboard")

    try:
        subscription = Subscription.objects.get(organization=organization)
    except Subscription.DoesNotExist:
        messages.warning(request, "No active subscription found.")
        subscription = None

    # Get plan limits and current usage
    plan_limits = get_plan_limits(subscription.plan if subscription else "free")
    current_usage = get_current_usage(organization, subscription)

    # Calculate trial days remaining
    trial_days_remaining = 0
    if subscription and subscription.current_period_end:
        days_remaining = (subscription.current_period_end - timezone.now().date()).days
        trial_days_remaining = max(0, days_remaining)

    # Get recent invoices (billing invoices)
    recent_invoices = Invoice.objects.filter(organization=organization).order_by(
        "-created_at"
    )[:10]

    context = {
        "page_title": "Billing & Subscription",
        "organization": organization,
        "subscription": subscription,
        "plan_limits": plan_limits,
        "current_usage": current_usage,
        "trial_days_remaining": trial_days_remaining,
        "recent_invoices": recent_invoices,
        "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
    }

    return render(request, "billing/dashboard.html", context)


@login_required(login_url="organizations:login")
def plan_upgrade_view(request):
    """
    Plan upgrade interface.
    """
    organization = get_user_organization(request.user)
    if not organization:
        messages.error(request, "No organization found.")
        return redirect("core:dashboard")

    if request.method == "POST":
        new_plan = request.POST.get("plan", "").lower()
        if new_plan not in ["starter", "professional", "enterprise"]:
            messages.error(request, "Invalid plan selected.")
            return redirect("organizations:upgrade")

        # For paid plans, check if customer has a payment method
        if new_plan != "free":
            # Create Stripe customer if doesn't exist
            if not organization.stripe_customer_id:
                try:
                    SubscriptionManager.create_customer(organization)
                except Exception as e:
                    logger.error(
                        f"Failed to create Stripe customer for {organization.slug}: {str(e)}"
                    )
                    messages.error(
                        request, "Failed to process payment. Please try again."
                    )
                    return redirect("organizations:upgrade")

            # Check if customer has payment methods
            try:
                import stripe

                stripe.api_key = settings.STRIPE_API_KEY
                payment_methods = stripe.Customer.list_payment_methods(
                    organization.stripe_customer_id, type="card"
                )

                if not payment_methods.data:
                    messages.warning(
                        request,
                        f"Please add a payment method before upgrading to {new_plan.title()} plan.",
                    )
                    return redirect("organizations:payment_method")
            except Exception as e:
                logger.error(
                    f"Failed to check payment methods for {organization.slug}: {str(e)}"
                )
                messages.error(
                    request, "Failed to verify payment method. Please try again."
                )
                return redirect("organizations:upgrade")

        try:
            # Create/update subscription with Stripe
            subscription = SubscriptionManager.create_subscription(
                organization=organization, plan=new_plan
            )

            if subscription:
                messages.success(
                    request, f"Successfully upgraded to {new_plan.title()} plan!"
                )
                logger.info(f"Organization {organization.slug} upgraded to {new_plan}")
                return redirect("organizations:billing_dashboard")
            else:
                messages.error(
                    request, "Failed to upgrade subscription. Please try again."
                )
                return redirect("organizations:upgrade")

        except Exception as e:
            logger.error(f"Upgrade error for {organization.slug}: {str(e)}")
            messages.error(request, f"Error processing upgrade: {str(e)}")
            return redirect("organizations:upgrade")

    # GET request - show available plans
    try:
        subscription = Subscription.objects.get(organization=organization)
        current_plan = subscription.plan
    except Subscription.DoesNotExist:
        subscription = None
        current_plan = "free"

    plans_data = get_plans_data()

    context = {
        "page_title": "Upgrade Plan",
        "organization": organization,
        "current_plan": current_plan,
        "plans": plans_data,
        "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
    }

    return render(request, "billing/upgrade.html", context)


@login_required(login_url="organizations:login")
def payment_method_view(request):
    """
    Manage payment methods.
    """
    organization = get_user_organization(request.user)
    if not organization:
        messages.error(request, "No organization found.")
        return redirect("core:dashboard")

    try:
        subscription = Subscription.objects.get(organization=organization)
    except Subscription.DoesNotExist:
        subscription = None

    context = {
        "page_title": "Payment Method",
        "organization": organization,
        "subscription": subscription,
        "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
    }

    return render(request, "billing/payment_method.html", context)


@login_required(login_url="organizations:login")
def invoice_history_view(request):
    """
    Billing invoice history.
    """
    organization = get_user_organization(request.user)
    if not organization:
        messages.error(request, "No organization found.")
        return redirect("core:dashboard")

    invoices = Invoice.objects.filter(organization=organization).order_by("-created_at")

    # Pagination
    from django.core.paginator import Paginator

    paginator = Paginator(invoices, 20)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "page_title": "Invoice History",
        "organization": organization,
        "page_obj": page_obj,
        "invoices": page_obj.object_list,
    }

    return render(request, "billing/invoice_history.html", context)


def get_plan_limits(plan):
    """
    Get feature limits for a given plan.
    """
    limits = {
        "free": {
            "name": "Free",
            "price": "$0",
            "invoices_per_month": 50,
            "max_users": 1,
            "features": [
                "Basic invoicing",
                "Up to 50 invoices/month",
                "1 team member",
                "Email support",
            ],
        },
        "starter": {
            "name": "Starter",
            "price": "$29",
            "invoices_per_month": 1000,
            "max_users": 5,
            "features": [
                "Professional invoicing",
                "Up to 1,000 invoices/month",
                "5 team members",
                "Payment tracking",
                "Email & chat support",
            ],
        },
        "professional": {
            "name": "Professional",
            "price": "$79",
            "invoices_per_month": None,  # Unlimited
            "max_users": 25,
            "features": [
                "Unlimited invoices",
                "Unlimited team members",
                "Advanced reporting",
                "API access",
                "Custom branding",
                "Priority support",
            ],
        },
        "enterprise": {
            "name": "Enterprise",
            "price": "Custom",
            "invoices_per_month": None,
            "max_users": None,
            "features": [
                "Everything in Professional",
                "Custom integrations",
                "Dedicated support",
                "SLA guarantee",
                "On-premise option",
            ],
        },
    }
    return limits.get(plan, limits["free"])


def get_plans_data():
    """
    Get all available plans for upgrade selection.
    """
    return {
        "free": get_plan_limits("free"),
        "starter": get_plan_limits("starter"),
        "professional": get_plan_limits("professional"),
        "enterprise": get_plan_limits("enterprise"),
    }


def get_current_usage(organization, subscription):
    """
    Calculate current usage vs. limits.
    """
    if not subscription:
        return {"invoices": 0, "users": 0, "percentage_used": 0}

    plan_limits = get_plan_limits(subscription.plan)

    # Count current invoices this month
    from datetime import date

    today = date.today()
    first_of_month = today.replace(day=1)

    invoices_this_month = Invoice.objects.filter(
        organization=organization, created_at__gte=first_of_month
    ).count()

    # Count team members
    team_members = OrganizationMember.objects.filter(organization=organization).count()

    # Calculate usage percentage
    limit = plan_limits["invoices_per_month"]
    if limit:
        percentage = int((invoices_this_month / limit) * 100)
    else:
        percentage = 0

    return {
        "invoices": invoices_this_month,
        "invoices_limit": limit if limit else "Unlimited",
        "users": team_members,
        "users_limit": (
            plan_limits["max_users"] if plan_limits["max_users"] else "Unlimited"
        ),
        "percentage_used": min(100, percentage),
    }
