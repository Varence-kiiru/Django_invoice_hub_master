{% comment %}
UPGRADE COMPONENTS USAGE GUIDE
==============================

This file documents how to use professional upgrade prompts throughout the system.

1. PLAN STATUS BANNER (Main Dashboard)
   - Location: Top of dashboard
   - Shows: Current plan, usage/limits, days remaining
   - CTA: "Upgrade →" button
   - Usage: {% include 'components/plan_status.html' %}
   - Requirements: subscription, current_usage, trial_days_remaining in context

2. QUOTA WARNING (Before Quota Hit)
   - Shows at 80% usage
   - Yellow warning banner with orange CTA
   - Usage: {% include 'components/quota_warning.html' %}
   - Requirements: quota_check with reason='near_quota' in context

3. FEATURE GATE (Pro/Enterprise Features)
   - Shows when accessing premium features
   - Purple gradient with "Unlock Feature" button
   - Usage: {% include 'components/feature_gate.html' with title="Feature Name" description="What this does" %}
   - Works with any feature-gated view

INTEGRATION EXAMPLES
====================

A. Add to Dashboard (DONE)
   - Plan status banner shows at top
   - Shows current tier + usage + trial timer
   
B. Add to Invoice Create (DONE)
   - Quota warning appears before form if at 80%+
   - Warns user before they hit hard limit
   
C. Add to Reports Page (Example)
   Form a feature-gated view:
   
   # In views.py
   from invoicing_app.organizations.plan_enforcer import PlanEnforcer
   
   @login_required
   def reports_view(request):
       org, plan, sub = PlanEnforcer.get_organization_plan(request.user)
       
       # Check if user has access
       if not PlanEnforcer.can_access_feature(plan, 'advanced_reporting'):
           context = {
               'feature_name': 'Advanced Reports',
               'required_plan': 'Professional'
           }
           return render(request, 'feature_gate_template.html', context)
       
       # Show reports
       return render(request, 'reports.html', context)
   
   # In template
   {% if not has_access %}
       {% include 'components/feature_gate.html' with 
           title="Advanced Reports" 
           description="Get detailed financial insights with our professional reporting tools"
       %}
   {% else %}
       <!-- Show reports -->
   {% endif %}

D. Usage in Any Template
   
   Display current plan info:
   {% if subscription %}
       <span>Current Plan: {{ subscription.get_plan_display }}</span>
   {% endif %}
   
   Show upgrade link anywhere:
   <a href="{% url 'organizations:upgrade' %}">Upgrade Your Plan</a>

QUOTA CHECK FLOW
================

1. User on FREE plan with 50/50 invoices
   ↓
2. Tries to create 51st invoice in same month
   ↓
3. @check_invoice_quota decorator intercepts
   ↓
4. Shows error: "Quota reached. Upgrade your plan"
   ↓
5. Redirects to organizations:upgrade page
   ↓
6. User sees 4 plan options with features
   ↓
7. User chooses plan and upgrades

NEAR-QUOTA WARNING FLOW
======================

1. User on FREE plan with 40/50 invoices
   ↓
2. Goes to create invoice page
   ↓
3. Page shows: "⚠️ Invoice Quota: 40/50 - 80% used"
   ↓
4. User can still create (no hard block)
   ↓
5. Click "Upgrade Plan →" to see options

STYLING NOTES
=============

All components use:
- Gradient headers (purple #667eea to #764ba2)
- Responsive design (mobile-optimized)
- Inline CSS for email compatibility
- Accessible color contrast
- Smooth transitions and hover states

Components automatically include all CSS, no extra styling needed.

COMPONENT FILES
===============

1. /templates/components/plan_status.html
   - Plan tier badge
   - Usage bar with progress
   - Renewal date
   - Upgrade button

2. /templates/components/quota_warning.html
   - Yellow warning banner
   - Current/limit display
   - Direct upgrade link

3. /templates/components/feature_gate.html
   - Purple gradient header
   - Feature icon + title
   - Unlock button

All components are self-contained with inline styles.
{% endcomment %}
