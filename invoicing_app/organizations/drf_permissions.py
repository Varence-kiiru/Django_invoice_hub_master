"""
Custom DRF permissions for plan enforcement.
"""
from rest_framework import permissions
from .plan_enforcer import PlanEnforcer


class InvoiceCreatePermission(permissions.BasePermission):
    """
    Allows invoice creation only if user hasn't exceeded their quota.
    """
    message = 'You have reached your invoice quota for this month. Please upgrade your plan.'
    
    def has_permission(self, request, view):
        # Allow read-only requests
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check invoice creation quota for POST/PUT/PATCH
        if request.method in ['POST', 'PUT', 'PATCH'] and 'invoice' in view.__class__.__name__.lower():
            quota_check = PlanEnforcer.check_invoice_quota(request.user)
            
            if not quota_check['allowed'] and quota_check.get('reason') == 'quota_exceeded':
                self.message = quota_check.get('message', self.message)
                return False
        
        return True


class TeamMemberPermission(permissions.BasePermission):
    """
    Allows team member addition only if organization hasn't exceeded their quota.
    """
    message = 'You have reached your team member quota. Please upgrade your plan.'
    
    def has_permission(self, request, view):
        # Allow read-only requests
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check team member quota for POST/PUT/PATCH
        if request.method in ['POST', 'PUT', 'PATCH'] and 'member' in view.__class__.__name__.lower():
            from .views_billing import get_user_organization
            
            organization = get_user_organization(request.user)
            if organization:
                quota_check = PlanEnforcer.check_team_member_quota(organization)
                
                if not quota_check['allowed'] and quota_check.get('reason') == 'quota_exceeded':
                    self.message = quota_check.get('message', self.message)
                    return False
        
        return True


class FeatureAccessPermission(permissions.BasePermission):
    """
    Restricts access to features based on plan tier.
    """
    
    def has_permission(self, request, view):
        """
        Checks if user's plan has access to the requested feature.
        Add this to views that are plan-restricted.
        """
        # Get user's plan
        organization, plan, subscription = PlanEnforcer.get_organization_plan(request.user)
        
        # If view has a 'required_feature' attribute, check access
        if hasattr(view, 'required_feature'):
            feature = view.required_feature
            if not PlanEnforcer.can_access_feature(plan, feature):
                self.message = f'This feature is not available in your {plan} plan. Please upgrade.'
                return False
        
        return True
