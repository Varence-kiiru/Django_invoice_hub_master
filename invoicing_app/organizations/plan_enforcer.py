"""
Plan enforcement and quota checking for subscriptions.
Ensures users don't exceed their plan limits.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from datetime import date
import logging

from .models import Subscription, Organization, OrganizationMember
from invoicing_app.invoices.models import Invoice

logger = logging.getLogger(__name__)


class PlanEnforcer:
    """
    Enforces plan limits and quotas.
    """
    
    # Plan limits mapping
    PLAN_LIMITS = {
        'free': {
            'invoices_per_month': 50,
            'max_team_members': 1,
            'features': ['basic_invoicing']
        },
        'starter': {
            'invoices_per_month': 1000,
            'max_team_members': 5,
            'features': ['basic_invoicing', 'delivery_tracking', 'team_collaboration']
        },
        'professional': {
            'invoices_per_month': None,  # Unlimited
            'max_team_members': 25,
            'features': ['advanced_invoicing', 'api_access', 'custom_branding', 'priority_support']
        },
        'enterprise': {
            'invoices_per_month': None,  # Unlimited
            'max_team_members': None,  # Unlimited
            'features': ['everything', 'dedicated_support', 'sla']
        }
    }
    
    @staticmethod
    def get_organization_plan(user):
        """
        Get user's organization and their subscription plan.
        Returns: (organization, plan_slug, subscription)
        """
        try:
            member = OrganizationMember.objects.select_related(
                'organization'
            ).get(user=user, is_primary=True)
            organization = member.organization
        except OrganizationMember.DoesNotExist:
            return None, 'free', None
        
        try:
            subscription = Subscription.objects.get(organization=organization)
            plan = subscription.plan
        except Subscription.DoesNotExist:
            subscription = None
            plan = 'free'
        
        return organization, plan, subscription
    
    @staticmethod
    def get_invoice_count_this_month(organization):
        """
        Get count of invoices created this month for the organization.
        Filters through organization members (created_by field on Invoice).
        """
        today = date.today()
        first_of_month = today.replace(day=1)
        
        # Get all member IDs in this organization
        member_ids = OrganizationMember.objects.filter(
            organization=organization
        ).values_list('user_id', flat=True)
        
        # Count invoices created by any member of the organization
        return Invoice.objects.filter(
            created_by_id__in=member_ids,
            created_at__gte=first_of_month
        ).count()
    
    @staticmethod
    def check_invoice_quota(user):
        """
        Check if user can create another invoice.
        
        Returns:
            dict: {
                'allowed': bool,
                'current_count': int,
                'limit': int or None,
                'message': str or None,
                'plan': str
            }
        """
        organization, plan, subscription = PlanEnforcer.get_organization_plan(user)
        
        if not organization:
            return {
                'allowed': False,
                'reason': 'No organization found',
                'plan': None
            }
        
        limits = PlanEnforcer.PLAN_LIMITS.get(plan, PlanEnforcer.PLAN_LIMITS['free'])
        limit = limits['invoices_per_month']
        current_count = PlanEnforcer.get_invoice_count_this_month(organization)
        
        # Unlimited plans
        if limit is None:
            return {
                'allowed': True,
                'current_count': current_count,
                'limit': None,
                'message': None,
                'plan': plan
            }
        
        # Check if limit exceeded
        if current_count >= limit:
            return {
                'allowed': False,
                'current_count': current_count,
                'limit': limit,
                'message': f'Invoice quota reached ({current_count}/{limit} this month). Upgrade your plan to create more.',
                'plan': plan,
                'reason': 'quota_exceeded'
            }
        
        # Warning at 80% usage
        percentage = (current_count / limit) * 100
        if percentage >= 80:
            return {
                'allowed': True,
                'current_count': current_count,
                'limit': limit,
                'message': f'Warning: You have used {current_count}/{limit} invoices this month ({int(percentage)}%). Consider upgrading.',
                'plan': plan,
                'reason': 'near_quota'
            }
        
        return {
            'allowed': True,
            'current_count': current_count,
            'limit': limit,
            'message': None,
            'plan': plan
        }
    
    @staticmethod
    def check_team_member_quota(organization):
        """
        Check if organization can add more team members.
        
        Returns:
            dict: {
                'allowed': bool,
                'current_count': int,
                'limit': int or None,
                'message': str or None
            }
        """
        plan = organization.plan if hasattr(organization, 'plan') else 'free'
        
        try:
            subscription = Subscription.objects.get(organization=organization)
            plan = subscription.plan
        except Subscription.DoesNotExist:
            plan = 'free'
        
        limits = PlanEnforcer.PLAN_LIMITS.get(plan, PlanEnforcer.PLAN_LIMITS['free'])
        limit = limits['max_team_members']
        
        current_count = OrganizationMember.objects.filter(
            organization=organization
        ).count()
        
        # Unlimited plans
        if limit is None:
            return {
                'allowed': True,
                'current_count': current_count,
                'limit': None,
                'message': None
            }
        
        # Check if limit exceeded
        if current_count >= limit:
            return {
                'allowed': False,
                'current_count': current_count,
                'limit': limit,
                'message': f'Team member limit reached ({current_count}/{limit}). Upgrade your plan to add more members.',
                'reason': 'quota_exceeded'
            }
        
        # Warning at 80% usage
        if current_count >= int(limit * 0.8):
            return {
                'allowed': True,
                'current_count': current_count,
                'limit': limit,
                'message': f'Warning: You have {current_count}/{limit} team members. Consider upgrading.',
                'reason': 'near_quota'
            }
        
        return {
            'allowed': True,
            'current_count': current_count,
            'limit': limit,
            'message': None
        }
    
    @staticmethod
    def can_access_feature(plan, feature):
        """
        Check if a plan tier has access to a feature.
        
        Args:
            plan: Plan slug ('free', 'starter', 'professional', 'enterprise')
            feature: Feature name ('api_access', 'custom_branding', etc.)
        
        Returns:
            bool: True if feature is available in plan
        """
        limits = PlanEnforcer.PLAN_LIMITS.get(plan, PlanEnforcer.PLAN_LIMITS['free'])
        return feature in limits.get('features', [])


def check_invoice_quota(view_func):
    """
    Decorator to check invoice quota before allowing invoice creation.
    
    Usage:
        @login_required
        @check_invoice_quota
        def create_invoice_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        quota_check = PlanEnforcer.check_invoice_quota(request.user)
        
        # Block creation if quota exceeded
        if not quota_check['allowed'] and quota_check.get('reason') == 'quota_exceeded':
            messages.error(request, quota_check['message'])
            logger.warning(
                f"User {request.user.id} attempted to create invoice but quota exceeded. "
                f"Plan: {quota_check['plan']}, "
                f"Used: {quota_check['current_count']}/{quota_check['limit']}"
            )
            return redirect('organizations:upgrade')
        
        # Warn if near quota (but allow)
        if quota_check.get('reason') == 'near_quota':
            messages.warning(request, quota_check['message'])
        
        # Store quota info in request for view to use
        request.quota_check = quota_check
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def check_team_member_quota(view_func):
    """
    Decorator to check team member quota before adding members.
    
    Usage:
        @login_required
        @check_team_member_quota
        def add_team_member_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from .views_billing import get_user_organization
        
        organization = get_user_organization(request.user)
        if not organization:
            messages.error(request, "No organization found.")
            return redirect('core:dashboard')
        
        quota_check = PlanEnforcer.check_team_member_quota(organization)
        
        # Block addition if quota exceeded
        if not quota_check['allowed'] and quota_check.get('reason') == 'quota_exceeded':
            messages.error(request, quota_check['message'])
            logger.warning(
                f"Organization {organization.slug} attempted to add team member but quota exceeded. "
                f"Used: {quota_check['current_count']}/{quota_check['limit']}"
            )
            return redirect('organizations:upgrade')
        
        # Warn if near quota (but allow)
        if quota_check.get('reason') == 'near_quota':
            messages.warning(request, quota_check['message'])
        
        # Store quota info in request
        request.quota_check = quota_check
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
