"""
Client management HTML views for Week 3 implementation.
Provides CRUD operations and account management for clients.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta

from invoicing_app.clients.models import Client, ClientAddress, ClientContact
from invoicing_app.clients.forms import ClientForm, ClientAddressForm, ClientContactForm
from invoicing_app.invoices.models import Invoice
from invoicing_app.payments.models import Payment


@login_required
def clients_list_view(request):
    """
    List all clients with search, filter, and pagination.
    Displays client information, invoice count, outstanding balance.
    """
    from invoicing_app.core.search_filters import (
        AdvancedFilterBuilder, FullTextSearch, parse_url_filters
    )
    from invoicing_app.core.models import SavedFilter
    
    clients_qs = Client.objects.all()
    
    # Parse URL filters
    criteria = parse_url_filters(request.GET)
    
    # Apply advanced filters
    if criteria:
        clients_qs = AdvancedFilterBuilder.apply_client_filters(clients_qs, criteria)
    
    # Apply full-text search
    search_query = request.GET.get('q', '')
    if search_query:
        clients_qs = FullTextSearch.search_clients(clients_qs, search_query)
    
    # Legacy search parameter support
    legacy_search = request.GET.get('search', '')
    if legacy_search and not search_query:
        clients_qs = FullTextSearch.search_clients(clients_qs, legacy_search)
        search_query = legacy_search
    
    # Annotate with invoice metrics
    clients_qs = clients_qs.annotate(
        invoice_count=Count('invoices'),
        outstanding_amount=Sum('invoices__amount_due')
    ).order_by('-created_at')
    
    # Get user's saved filters
    user_filters = SavedFilter.get_user_filters(request.user, 'client')
    
    # Pagination
    paginator = Paginator(clients_qs, 25)
    page_number = request.GET.get('page', 1)
    clients = paginator.get_page(page_number)
    
    context = {
        'clients': clients,
        'search_query': search_query,
        'current_filters': criteria,
        'user_filters': user_filters,
        'page_obj': clients,
        'name': request.GET.get('name', ''),
        'email': request.GET.get('email', ''),
        'phone': request.GET.get('phone', ''),
        'client_type': request.GET.get('client_type', ''),
        'is_active': request.GET.get('is_active', ''),
        'has_invoices': request.GET.get('has_invoices', ''),
    }
    return render(request, '4_clients/clients_list.html', context)


@login_required
def clients_create_view(request):
    """
    Create a new client with form validation.
    Handles client contact and address information.
    """
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.created_by = request.user
            client.save()
            return redirect('clients:detail', pk=client.id)
    else:
        form = ClientForm()
    
    context = {'form': form}
    return render(request, '4_clients/clients_create.html', context)


@login_required
def clients_edit_view(request, pk):
    """
    Edit an existing client's information.
    """
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            client = form.save()
            return redirect('clients:detail', pk=client.id)
    else:
        form = ClientForm(instance=client)
    
    context = {'client': client, 'form': form}
    return render(request, '4_clients/clients_edit.html', context)


@login_required
def clients_detail_view(request, pk):
    """
    View complete client profile with invoices, payments, and contacts.
    """
    client = get_object_or_404(Client, pk=pk)
    invoices = client.invoices.filter(is_active=True)[:10]
    payments = Payment.objects.filter(invoice__client=client).order_by('-payment_date')[:10]
    addresses = client.addresses.all()
    contacts = client.contacts.all()
    
    # Calculate totals
    total_invoiced = client.invoices.filter(is_active=True).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_paid = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    # Outstanding = any invoice with amount_due > 0 (not filtered by status, as unpaid invoices can have any status)
    outstanding = client.invoices.filter(is_active=True, amount_due__gt=0).aggregate(Sum('amount_due'))['amount_due__sum'] or 0
    invoice_count = client.invoices.filter(is_active=True).count()
    
    context = {
        'client': client,
        'recent_invoices': invoices,
        'recent_payments': payments,
        'addresses': addresses,
        'contacts': contacts,
        'total_invoiced': total_invoiced,
        'total_paid': total_paid,
        'outstanding': outstanding,
        'invoice_count': invoice_count,
    }
    return render(request, '4_clients/clients_detail.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def clients_delete_view(request, pk):
    """
    Delete or soft-delete a client.
    """
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        # Soft delete
        client.is_active = False
        client.save()
        return redirect('clients-list')
    
    context = {'client': client}
    return render(request, '4_clients/clients_delete_confirm.html', context)


@login_required
def client_addresses_view(request, pk):
    """
    Manage client addresses (billing, shipping, etc).
    """
    client = get_object_or_404(Client, pk=pk)
    addresses = client.addresses.all()
    
    if request.method == 'POST':
        form = ClientAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.client = client
            address.save()
            return redirect('clients:addresses', pk=client.id)
    else:
        form = ClientAddressForm()
    
    context = {
        'client': client,
        'addresses': addresses,
        'form': form,
    }
    return render(request, '4_clients/client_addresses.html', context)


@login_required
def client_contacts_view(request, pk):
    """
    Manage client contacts (decision makers, primary contact, etc).
    """
    client = get_object_or_404(Client, pk=pk)
    contacts = client.contacts.all()
    
    if request.method == 'POST':
        form = ClientContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.client = client
            contact.save()
            return redirect('clients:contacts', pk=client.id)
    else:
        form = ClientContactForm()
    
    context = {
        'client': client,
        'contacts': contacts,
        'form': form,
    }
    return render(request, '4_clients/client_contacts.html', context)


@login_required
def client_statements_view(request, pk):
    """
    Display client account statement (A/R aging).
    Shows invoice history, payments, and outstanding balance.
    """
    client = get_object_or_404(Client, pk=pk)
    
    # Get all invoices
    invoices = client.invoices.filter(is_active=True).order_by('-invoice_date')
    
    # Get all payments
    payments = Payment.objects.filter(invoice__client=client).order_by('-payment_date')
    
    # Calculate aging buckets
    today = timezone.now().date()
    aging = {
        'current': invoices.filter(due_date__gte=today).exclude(status='paid').count(),
        '30_days': invoices.filter(
            due_date__lt=today,
            due_date__gte=today - timedelta(days=30),
        ).exclude(status='paid').count(),
        '60_days': invoices.filter(
            due_date__lt=today - timedelta(days=30),
            due_date__gte=today - timedelta(days=60),
        ).exclude(status='paid').count(),
        'over_90': invoices.filter(
            due_date__lt=today - timedelta(days=90),
        ).exclude(status='paid').count(),
    }
    
    # Calculate totals
    total_invoiced = invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_paid = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    outstanding = invoices.exclude(status='paid').aggregate(Sum('amount_due'))['amount_due__sum'] or 0
    
    context = {
        'client': client,
        'invoices': invoices,
        'payments': payments,
        'aging': aging,
        'total_invoiced': total_invoiced,
        'total_paid': total_paid,
        'outstanding': outstanding,
    }
    return render(request, '4_clients/client_statements.html', context)


@login_required
@require_http_methods(["POST"])
def address_delete_view(request, pk):
    """Delete a client address (soft delete)."""
    address = get_object_or_404(ClientAddress, pk=pk)
    client_id = address.client.id
    address.delete()
    return redirect('clients:addresses', pk=client_id)


@login_required
@require_http_methods(["POST"])
def contact_delete_view(request, pk):
    """Delete a client contact (soft delete)."""
    contact = get_object_or_404(ClientContact, pk=pk)
    client_id = contact.client.id
    contact.delete()
    return redirect('clients:contacts', pk=client_id)
