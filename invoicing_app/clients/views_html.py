"""
Client management HTML views for Week 3 implementation.
Provides CRUD operations and account management for clients.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from invoicing_app.clients.models import Client, ClientAddress, ClientContact
from invoicing_app.clients.forms import ClientForm, ClientAddressForm, ClientContactForm
from invoicing_app.payments.models import Payment
from invoicing_app.core.breadcrumb_config import BreadcrumbBuilder


@login_required
def clients_list_view(request):
    """
    List all clients with search, filter, and pagination.
    Displays client information, invoice count, outstanding balance.
    """
    from invoicing_app.core.search_filters import (
        AdvancedFilterBuilder,
        FullTextSearch,
        parse_url_filters,
    )
    from invoicing_app.core.models import SavedFilter

    clients_qs = Client.objects.all()

    # Parse URL filters
    criteria = parse_url_filters(request.GET)

    # Apply advanced filters
    if criteria:
        clients_qs = AdvancedFilterBuilder.apply_client_filters(clients_qs, criteria)

    # Apply full-text search
    search_query = request.GET.get("q", "")
    if search_query:
        clients_qs = FullTextSearch.search_clients(clients_qs, search_query)

    # Legacy search parameter support
    legacy_search = request.GET.get("search", "")
    if legacy_search and not search_query:
        clients_qs = FullTextSearch.search_clients(clients_qs, legacy_search)
        search_query = legacy_search

    # Annotate with invoice metrics
    clients_qs = clients_qs.annotate(
        invoice_count=Count("invoices"), outstanding_amount=Sum("invoices__amount_due")
    ).order_by("-created_at")

    # Get user's saved filters
    user_filters = SavedFilter.get_user_filters(request.user, "client")

    # Pagination
    paginator = Paginator(clients_qs, 25)
    page_number = request.GET.get("page", 1)
    clients = paginator.get_page(page_number)

    context = {
        "page_title": "Clients",
        "clients": clients,
        "search_query": search_query,
        "current_filters": criteria,
        "user_filters": user_filters,
        "page_obj": clients,
        "name": request.GET.get("name", ""),
        "email": request.GET.get("email", ""),
        "phone": request.GET.get("phone", ""),
        "client_type": request.GET.get("client_type", ""),
        "is_active": request.GET.get("is_active", ""),
        "has_invoices": request.GET.get("has_invoices", ""),
        "breadcrumbs": (BreadcrumbBuilder().add_home().add_current("Clients").build()),
    }
    return render(request, "4_clients/clients_list.html", context)


@login_required
def clients_create_view(request):
    """
    Create a new client with form validation.
    Handles client contact and address information.
    """
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.created_by = request.user
            client.save()
            return redirect("clients:detail", pk=client.id)
    else:
        form = ClientForm()

    # Get company settings for currency display
    from invoicing_app.core.models import CompanySettings

    company_settings = CompanySettings.get_settings()

    context = {
        "page_title": "New Client",
        "form": form,
        "company_settings": company_settings,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Clients", "clients:list")
            .add_current("New Client")
            .build()
        ),
    }
    return render(request, "4_clients/clients_create.html", context)


@login_required
def clients_edit_view(request, pk):
    """
    Edit an existing client's information.
    """
    client = get_object_or_404(Client, pk=pk)

    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            client = form.save()
            return redirect("clients:detail", pk=client.id)
    else:
        form = ClientForm(instance=client)

    # Get company settings for currency display
    from invoicing_app.core.models import CompanySettings

    company_settings = CompanySettings.get_settings()

    context = {
        "page_title": "Edit Client",
        "client": client,
        "form": form,
        "company_settings": company_settings,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Clients", "clients:list")
            .add(f"Client: {client.name}", "clients:detail", url_kwargs={"pk": pk})
            .add_current("Edit")
            .build()
        ),
    }
    return render(request, "4_clients/clients_edit.html", context)


@login_required
def clients_detail_view(request, pk):
    """
    View complete client profile with invoices, payments, and contacts.
    """
    client = get_object_or_404(Client, pk=pk)
    invoices = client.invoices.filter(is_active=True)[:10]
    payments = Payment.objects.filter(invoice__client=client).order_by("-payment_date")[
        :10
    ]
    addresses = client.addresses.all()
    contacts = client.contacts.all()

    # Calculate totals
    total_invoiced = (
        client.invoices.filter(is_active=True).aggregate(Sum("total_amount"))[
            "total_amount__sum"
        ]
        or 0
    )
    total_paid = payments.aggregate(Sum("amount"))["amount__sum"] or 0
    # Outstanding = any invoice with amount_due > 0 (not filtered by status, as unpaid invoices can have any status)
    outstanding = (
        client.invoices.filter(is_active=True, amount_due__gt=0).aggregate(
            Sum("amount_due")
        )["amount_due__sum"]
        or 0
    )
    invoice_count = client.invoices.filter(is_active=True).count()

    context = {
        "page_title": client.name,
        "client": client,
        "recent_invoices": invoices,
        "recent_payments": payments,
        "addresses": addresses,
        "contacts": contacts,
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "outstanding": outstanding,
        "invoice_count": invoice_count,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Clients", "clients:list")
            .add_current(f"Client: {client.name}")
            .build()
        ),
    }
    return render(request, "4_clients/clients_detail.html", context)


@login_required
@require_http_methods(["POST"])
def clients_delete_view(request, pk):
    """Delete or soft-delete a client."""
    client = get_object_or_404(Client, pk=pk)
    # Soft delete
    client.is_active = False
    client.save()
    return redirect("clients-list")


@login_required
def client_addresses_view(request, pk):
    """
    Manage client addresses (billing, shipping, etc).
    """
    client = get_object_or_404(Client, pk=pk)
    addresses = client.addresses.all()

    if request.method == "POST":
        form = ClientAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.client = client
            address.save()
            return redirect("clients:addresses", pk=client.id)
    else:
        form = ClientAddressForm()

    context = {
        "page_title": "Addresses",
        "client": client,
        "addresses": addresses,
        "form": form,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Clients", "clients:list")
            .add(f"Client: {client.name}", "clients:detail", {"pk": client.id})
            .add_current("Addresses")
            .build()
        ),
    }
    return render(request, "4_clients/client_addresses.html", context)


@login_required
def address_form_view(request, client_pk, address_pk=None):
    """
    Add or edit a client address on a dedicated form page.
    """
    client = get_object_or_404(Client, pk=client_pk)
    address = None
    if address_pk:
        address = get_object_or_404(ClientAddress, pk=address_pk, client=client)

    if request.method == "POST":
        form = ClientAddressForm(request.POST, instance=address)
        if form.is_valid():
            address_obj = form.save(commit=False)
            address_obj.client = client
            address_obj.save()
            return redirect("clients:addresses", pk=client.id)
    else:
        form = ClientAddressForm(instance=address)

    page_title = f"{'Edit' if address else 'Add'} Address"
    context = {
        "page_title": page_title,
        "client": client,
        "address": address,
        "form": form,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Clients", "clients:list")
            .add(f"Client: {client.name}", "clients:detail", {"pk": client.id})
            .add("Addresses", "clients:addresses", {"pk": client.id})
            .add_current(page_title)
            .build()
        ),
    }
    return render(request, "4_clients/client_address_form.html", context)


@login_required
def client_contacts_view(request, pk):
    """
    Manage client contacts (decision makers, primary contact, etc).
    """
    client = get_object_or_404(Client, pk=pk)
    contacts = client.contacts.all()

    if request.method == "POST":
        form = ClientContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.client = client
            contact.save()
            return redirect("clients:contacts", pk=client.id)
    else:
        form = ClientContactForm()

    context = {
        "page_title": "Contacts",
        "client": client,
        "contacts": contacts,
        "form": form,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Clients", "clients:list")
            .add(f"Client: {client.name}", "clients:detail", {"pk": client.id})
            .add_current("Contacts")
            .build()
        ),
    }
    return render(request, "4_clients/client_contacts.html", context)


@login_required
def contact_form_view(request, client_pk, contact_pk=None):
    """
    Add or edit a client contact on a dedicated form page.
    """
    client = get_object_or_404(Client, pk=client_pk)
    contact = None
    if contact_pk:
        contact = get_object_or_404(ClientContact, pk=contact_pk, client=client)

    if request.method == "POST":
        form = ClientContactForm(request.POST, instance=contact)
        if form.is_valid():
            contact_obj = form.save(commit=False)
            contact_obj.client = client
            contact_obj.save()
            return redirect("clients:contacts", pk=client.id)
    else:
        form = ClientContactForm(instance=contact)

    page_title = f"{'Edit' if contact else 'Add'} Contact"
    context = {
        "page_title": page_title,
        "client": client,
        "contact": contact,
        "form": form,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Clients", "clients:list")
            .add(f"Client: {client.name}", "clients:detail", {"pk": client.id})
            .add("Contacts", "clients:contacts", {"pk": client.id})
            .add_current(page_title)
            .build()
        ),
    }
    return render(request, "4_clients/client_contact_form.html", context)


@login_required
def client_statements_view(request, pk):
    """
    Display client account statement (A/R aging).
    Shows invoice history, payments, and outstanding balance.
    """
    client = get_object_or_404(Client, pk=pk)

    # Get all invoices
    invoices = client.invoices.filter(is_active=True).order_by("-invoice_date")

    # Get all payments
    payments = Payment.objects.filter(invoice__client=client).order_by("-payment_date")

    # Calculate aging buckets
    today = timezone.now().date()
    aging = {
        "current": invoices.filter(due_date__gte=today).exclude(status="paid").count(),
        "30_days": invoices.filter(
            due_date__lt=today,
            due_date__gte=today - timedelta(days=30),
        )
        .exclude(status="paid")
        .count(),
        "60_days": invoices.filter(
            due_date__lt=today - timedelta(days=30),
            due_date__gte=today - timedelta(days=60),
        )
        .exclude(status="paid")
        .count(),
        "over_90": invoices.filter(
            due_date__lt=today - timedelta(days=90),
        )
        .exclude(status="paid")
        .count(),
    }

    # Calculate totals
    total_invoiced = invoices.aggregate(Sum("total_amount"))["total_amount__sum"] or 0
    total_paid = payments.aggregate(Sum("amount"))["amount__sum"] or 0
    outstanding = (
        invoices.exclude(status="paid").aggregate(Sum("amount_due"))["amount_due__sum"]
        or 0
    )

    context = {
        "page_title": "A/R Statement",
        "client": client,
        "invoices": invoices,
        "payments": payments,
        "aging": aging,
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "outstanding": outstanding,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Clients", "clients:list")
            .add(f"Client: {client.name}", "clients:detail", {"pk": client.id})
            .add_current("Statement")
            .build()
        ),
    }
    return render(request, "4_clients/client_statements.html", context)


@login_required
@require_http_methods(["POST"])
def address_delete_view(request, pk):
    """Delete a client address."""
    address = get_object_or_404(ClientAddress, pk=pk)
    client_id = address.client.id
    address.delete()
    return redirect("clients:addresses", pk=client_id)


@login_required
@require_http_methods(["POST"])
def contact_delete_view(request, pk):
    """Delete a client contact."""
    contact = get_object_or_404(ClientContact, pk=pk)
    client_id = contact.client.id
    contact.delete()
    return redirect("clients:contacts", pk=client_id)
    return render(request, "4_clients/client_contact_delete_confirm.html", context)
