"""
Tax rate management HTML views with full CRUD operations.
Provides professional interface for managing tax rates and VAT rules.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q

from invoicing_app.core.views_html import role_required
from .models import TaxRate, VATRule
from .forms import TaxRateForm, VATRuleForm


@login_required
def tax_rates_list(request):
    """
    List all tax rates with search, filter, and pagination.
    Shows both active and inactive rates.
    """
    tax_rates_qs = TaxRate.objects.all().order_by('-effective_from', 'code')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        tax_rates_qs = tax_rates_qs.filter(
            Q(code__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(country__icontains=search_query)
        )
    
    # Filter by tax type
    tax_type_filter = request.GET.get('tax_type', '')
    if tax_type_filter:
        tax_rates_qs = tax_rates_qs.filter(tax_type=tax_type_filter)
    
    # Filter by status (active/inactive)
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        from django.utils import timezone
        today = timezone.now().date()
        tax_rates_qs = tax_rates_qs.filter(effective_from__lte=today).exclude(
            effective_to__lt=today
        )
    elif status_filter == 'inactive':
        from django.utils import timezone
        today = timezone.now().date()
        tax_rates_qs = tax_rates_qs.filter(
            Q(effective_from__gt=today) | Q(effective_to__lt=today)
        )
    
    # Pagination
    paginator = Paginator(tax_rates_qs, 25)
    page_number = request.GET.get('page', 1)
    tax_rates = paginator.get_page(page_number)
    
    # Get tax type choices for filter dropdown
    tax_types = TaxRate.TAX_TYPE_CHOICES
    
    context = {
        'tax_rates': tax_rates,
        'search_query': search_query,
        'tax_type_filter': tax_type_filter,
        'status_filter': status_filter,
        'tax_types': tax_types,
        'page_obj': tax_rates,
        'page_title': 'Tax Rates',
        'page_description': 'Manage all tax rates used in invoices',
    }
    return render(request, 'taxes/tax_rates_list.html', context)


@login_required
@role_required('Admin')
def tax_rate_create(request):
    """
    Create a new tax rate.
    Admin only.
    """
    if request.method == 'POST':
        form = TaxRateForm(request.POST)
        if form.is_valid():
            tax_rate = form.save()
            messages.success(request, f'Tax rate "{tax_rate.name}" created successfully!')
            return redirect('taxes:detail', pk=tax_rate.id)
    else:
        form = TaxRateForm()
    
    context = {
        'form': form,
        'page_title': 'Create Tax Rate',
        'action': 'create',
    }
    return render(request, 'taxes/tax_rate_form.html', context)


@login_required
def tax_rate_detail(request, pk):
    """
    View tax rate details with usage information.
    """
    tax_rate = get_object_or_404(TaxRate, pk=pk)
    
    # Get related VAT rules
    vat_rules = tax_rate.vat_rules.all()
    
    # Get related product tax classes
    related_products = tax_rate.products.all().count() if hasattr(tax_rate, 'products') else 0
    
    context = {
        'tax_rate': tax_rate,
        'vat_rules': vat_rules,
        'related_products': related_products,
        'page_title': f'Tax Rate - {tax_rate.name}',
    }
    return render(request, 'taxes/tax_rate_detail.html', context)


@login_required
@role_required('Admin')
def tax_rate_edit(request, pk):
    """
    Edit an existing tax rate.
    Admin only.
    """
    tax_rate = get_object_or_404(TaxRate, pk=pk)
    
    if request.method == 'POST':
        form = TaxRateForm(request.POST, instance=tax_rate)
        if form.is_valid():
            tax_rate = form.save()
            messages.success(request, f'Tax rate "{tax_rate.name}" updated successfully!')
            return redirect('taxes:detail', pk=tax_rate.id)
    else:
        form = TaxRateForm(instance=tax_rate)
    
    context = {
        'form': form,
        'tax_rate': tax_rate,
        'page_title': f'Edit Tax Rate - {tax_rate.name}',
        'action': 'edit',
    }
    return render(request, 'taxes/tax_rate_form.html', context)


@login_required
@role_required('Admin')
@require_http_methods(["GET", "POST"])
def tax_rate_delete(request, pk):
    """
    Delete a tax rate (soft delete by setting effective_to).
    Admin only.
    Shows confirmation page first.
    """
    tax_rate = get_object_or_404(TaxRate, pk=pk)
    
    # Check if tax rate is being used
    related_count = tax_rate.vat_rules.count()
    
    if request.method == 'POST':
        from django.utils import timezone
        tax_rate.effective_to = timezone.now().date()
        tax_rate.save()
        messages.success(request, f'Tax rate "{tax_rate.name}" has been deactivated.')
        return redirect('taxes:list')
    
    context = {
        'tax_rate': tax_rate,
        'related_count': related_count,
        'page_title': f'Delete Tax Rate - {tax_rate.name}',
    }
    return render(request, 'taxes/tax_rate_delete_confirm.html', context)


@login_required
@role_required('Admin')
def vat_rules_list(request):
    """
    List all VAT rules with stats and filtering.
    """
    vat_rules_qs = VATRule.objects.select_related(
        'tax_class', 'tax_rate'
    ).order_by('-priority', 'name')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        vat_rules_qs = vat_rules_qs.filter(
            Q(name__icontains=search_query) |
            Q(tax_class__name__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        vat_rules_qs = vat_rules_qs.filter(is_active=True)
    elif status_filter == 'inactive':
        vat_rules_qs = vat_rules_qs.filter(is_active=False)
    
    # Calculate stats on ALL rules (not filtered, for dashboard overview)
    total_rules = VATRule.objects.count()
    active_rules = VATRule.objects.filter(is_active=True).count()
    inactive_rules = VATRule.objects.filter(is_active=False).count()
    
    # Get tax classes count
    from invoicing_app.products.models import ProductTaxClass
    tax_classes_count = ProductTaxClass.objects.count()
    
    # Pagination
    paginator = Paginator(vat_rules_qs, 20)
    page_number = request.GET.get('page', 1)
    vat_rules_page = paginator.get_page(page_number)
    
    context = {
        'vat_rules': vat_rules_page,
        'search_query': search_query,
        'status': status_filter,
        'total_rules': total_rules,
        'active_rules': active_rules,
        'inactive_rules': inactive_rules,
        'tax_classes_count': tax_classes_count,
        'page_obj': vat_rules_page,
        'page_title': 'VAT Rules',
        'page_description': 'Manage VAT applicability rules',
        'is_paginated': vat_rules_page.has_other_pages(),
    }
    return render(request, 'taxes/vat_rules_list.html', context)


@login_required
@role_required('Admin')
@require_http_methods(["POST"])
def vat_rule_delete(request, pk):
    """
    Delete a VAT rule.
    Admin only. POST only for safety.
    """
    vat_rule = get_object_or_404(VATRule, pk=pk)
    
    if request.method == 'POST':
        rule_name = vat_rule.name
        vat_rule.delete()
        messages.success(request, f'VAT rule "{rule_name}" has been deleted.')
        return redirect('taxes:vat-rules-list')
    
    return redirect('taxes:vat-rules-list')


@login_required
@role_required('Admin')
def vat_rule_create(request):
    """
    Create a new VAT rule.
    Admin only.
    """
    if request.method == 'POST':
        form = VATRuleForm(request.POST)
        if form.is_valid():
            vat_rule = form.save()
            messages.success(request, f'VAT rule "{vat_rule.name}" created successfully!')
            return redirect('taxes:vat-rules-list')
    else:
        form = VATRuleForm()
    
    context = {
        'form': form,
        'page_title': 'Create VAT Rule',
        'action': 'create',
    }
    return render(request, 'taxes/vat_rule_form.html', context)


@login_required
@role_required('Admin')
def vat_rule_edit(request, pk):
    """
    Edit an existing VAT rule.
    Admin only.
    """
    vat_rule = get_object_or_404(VATRule, pk=pk)
    
    if request.method == 'POST':
        form = VATRuleForm(request.POST, instance=vat_rule)
        if form.is_valid():
            vat_rule = form.save()
            messages.success(request, f'VAT rule "{vat_rule.name}" updated successfully!')
            return redirect('taxes:vat-rules-list')
    else:
        form = VATRuleForm(instance=vat_rule)
    
    context = {
        'form': form,
        'vat_rule': vat_rule,
        'page_title': f'Edit VAT Rule - {vat_rule.name}',
        'action': 'edit',
    }
    return render(request, 'taxes/vat_rule_form.html', context)
