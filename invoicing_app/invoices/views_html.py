"""
Invoice management HTML views.
Provides CRUD operations and reporting for invoices.
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta
from functools import wraps

from invoicing_app.invoices.models import (
    Invoice,
    InvoiceLineItem,
)
from invoicing_app.invoices.services import InvoiceNumberService
from invoicing_app.clients.models import Client
from invoicing_app.products.models import Product
from invoicing_app.taxes.models import TaxRate
from invoicing_app.audit.models import AuditLog
from invoicing_app.core.models import CompanySettings
from invoicing_app.organizations.plan_enforcer import check_invoice_quota
from invoicing_app.core.breadcrumb_config import BreadcrumbBuilder

logger = logging.getLogger(__name__)


# ━━━━━ UTILITY FUNCTIONS ━━━━━


def _get_user_role(request):
    """Get user's role name from CustomUser or superuser."""
    if request.user.is_superuser:
        return "Admin"
    try:
        from invoicing_app.user_management.models import CustomUser

        cu = CustomUser.objects.select_related("role").get(user=request.user)
        return cu.role.name if cu.role else "User"
    except (ObjectDoesNotExist, AttributeError):
        return "User"


def role_required(*allowed_roles):
    """Decorator to check user role before allowing access."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("organizations:login")
            role = _get_user_role(request)
            if role not in allowed_roles:
                from django.contrib import messages

                messages.error(
                    request, "You do not have permission to access this page."
                )
                return redirect("core:dashboard")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def paginate_queryset(request, queryset, per_page=20):
    """Paginate a queryset based on request GET['page']."""
    paginator = Paginator(queryset, per_page)
    page = request.GET.get("page", 1)
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)
    return items


# ━━━━━ INVOICE MANAGEMENT VIEWS ━━━━━


@login_required
def invoices_list_view(request):
    """List all invoices with pagination and advanced filtering."""
    from invoicing_app.core.search_filters import (
        AdvancedFilterBuilder,
        FullTextSearch,
        parse_url_filters,
    )
    from invoicing_app.core.models import SavedFilter

    queryset = Invoice.objects.filter(is_active=True).select_related("client")

    # Parse URL filters
    criteria = parse_url_filters(request.GET)

    # Apply advanced filters
    if criteria:
        queryset = AdvancedFilterBuilder.apply_invoice_filters(queryset, criteria)

    # Apply full-text search
    search_query = request.GET.get("q", "")
    if search_query:
        queryset = FullTextSearch.search_invoices(queryset, search_query)

    # Legacy search parameter support
    legacy_search = request.GET.get("search", "")
    if legacy_search and not search_query:
        queryset = FullTextSearch.search_invoices(queryset, legacy_search)
        search_query = legacy_search

    # Get user's saved filters
    user_filters = SavedFilter.get_user_filters(request.user, "invoice")

    # Pagination
    invoices = paginate_queryset(
        request, queryset.order_by("-invoice_date"), per_page=20
    )

    context = {
        "page_title": "Invoices",
        "invoices": invoices,
        "search_query": search_query,
        "current_filters": criteria,
        "user_filters": user_filters,
        "status_list": request.GET.getlist("status"),
        "client_name": request.GET.get("client_name", ""),
        "invoice_number": request.GET.get("invoice_number", ""),
        "min_amount": request.GET.get("min_amount", ""),
        "max_amount": request.GET.get("max_amount", ""),
        "from_date": request.GET.get("from_date", ""),
        "to_date": request.GET.get("to_date", ""),
        "days_overdue": request.GET.get("days_overdue", ""),
        "status_choices": Invoice.STATUS_CHOICES,
        "breadcrumbs": (BreadcrumbBuilder().add_home().add_current("Invoices").build()),
    }
    return render(request, "6_invoices/invoices_list.html", context)


@login_required
@login_required
@check_invoice_quota
def invoices_create_view(request):
    """Create new invoice (draft)."""
    if request.method == "POST":
        try:
            from django.contrib import messages

            # Get the invoice prefix from company settings
            try:
                settings = CompanySettings.objects.get()
                prefix = settings.invoice_prefix
            except CompanySettings.DoesNotExist:
                prefix = "INV"  # Fallback to default

            # Generate invoice number using the service
            invoice_number = InvoiceNumberService.generate_next_number(prefix=prefix)

            today = timezone.now().date()
            invoice = Invoice.objects.create(
                invoice_number=invoice_number,
                client_id=request.POST.get("client"),
                invoice_date=today,
                due_date=request.POST.get("due_date") or (today + timedelta(days=30)),
                description=request.POST.get("description", "").strip(),
                currency=request.POST.get("currency", "KES"),
                created_by=request.user,
                updated_by=request.user,
            )

            messages.success(request, f"Invoice {invoice_number} created successfully!")
            return redirect("invoices:detail", pk=invoice.id)
        except Exception as e:
            from django.contrib import messages

            messages.error(request, f"Error creating invoice: {str(e)}")

    # Get quota info for display
    from invoicing_app.organizations.plan_enforcer import PlanEnforcer

    quota_check = PlanEnforcer.check_invoice_quota(request.user)

    context = {
        "page_title": "Create Invoice",
        "clients": Client.objects.filter(is_active=True),
        "quota_check": quota_check,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Invoices", "invoices:list")
            .add_current("New Invoice")
            .build()
        ),
    }
    return render(request, "6_invoices/invoices_create.html", context)


@login_required
def invoices_detail_view(request, pk):
    """View invoice details with line items."""
    invoice = get_object_or_404(Invoice, pk=pk, is_active=True)
    line_items = invoice.line_items.all()
    payments = invoice.payments.all()

    # Get associated deliveries
    from invoicing_app.deliveries.models import Delivery

    deliveries = Delivery.objects.filter(invoice=invoice, is_active=True).order_by(
        "-created_at"
    )

    # Check if user can create deliveries
    can_create_delivery = request.user.is_superuser or (
        hasattr(request.user, "custom_user")
        and "create_deliveries" in request.user.custom_user.get_permissions()
    )

    context = {
        "page_title": f"Invoice - {invoice.invoice_number}",
        "invoice": invoice,
        "line_items": line_items,
        "payments": payments,
        "deliveries": deliveries,
        "can_create_delivery": can_create_delivery,
        "can_edit": invoice.status == "draft",
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Invoices", "invoices:list")
            .add_current(f"Invoice: {invoice.invoice_number}")
            .build()
        ),
    }
    return render(request, "6_invoices/invoices_detail.html", context)


@login_required
def invoices_edit_view(request, pk):
    """Edit invoice (draft only)."""
    from django.contrib import messages

    invoice = get_object_or_404(Invoice, pk=pk, is_active=True, status="draft")

    if request.method == "POST":
        try:
            invoice.due_date = request.POST.get("due_date") or invoice.due_date
            invoice.description = request.POST.get("description", "").strip()
            invoice.updated_by = request.user
            invoice.save()

            messages.success(request, f"Invoice {invoice.invoice_number} updated!")
            return redirect("invoices:detail", pk=invoice.id)
        except Exception as e:
            messages.error(request, f"Error updating invoice: {str(e)}")

    context = {
        "page_title": f"Edit Invoice - {invoice.invoice_number}",
        "invoice": invoice,
        "clients": Client.objects.filter(is_active=True),
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Invoices", "invoices:list")
            .add(
                f"Invoice: {invoice.invoice_number}",
                "invoices:detail",
                url_kwargs={"pk": pk},
            )
            .add_current("Edit")
            .build()
        ),
    }
    return render(request, "6_invoices/invoices_edit.html", context)


@login_required
def invoices_view_view(request, pk):
    """View invoice (read-only, for clients/public)."""
    invoice = get_object_or_404(Invoice, pk=pk, is_active=True)
    line_items = invoice.line_items.all()

    context = {
        "page_title": f"Invoice {invoice.invoice_number}",
        "invoice": invoice,
        "line_items": line_items,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Invoices", "invoices:list")
            .add_current(f"Invoice: {invoice.invoice_number}")
            .build()
        ),
    }
    return render(request, "6_invoices/invoices_view.html", context)


@login_required
def invoice_line_items_view(request, pk):
    """Manage invoice line items."""
    import json

    invoice = get_object_or_404(Invoice, pk=pk, is_active=True, status="draft")
    line_items = invoice.line_items.all()

    # Get active tax rates (effective_from <= today and effective_to is null or >= today)
    today = timezone.now().date()
    active_tax_rates = (
        TaxRate.objects.filter(effective_from__lte=today)
        .filter(Q(effective_to__isnull=True) | Q(effective_to__gte=today))
        .order_by("tax_type", "rate_percentage")
    )

    # Build tax class to rate mapping for JavaScript
    # Group tax rates by tax_type (standard, zero, exempt)
    tax_class_rate_map = {}

    # For each tax type, find the active tax rate
    for tax_type in ["standard", "zero", "exempt"]:
        rates = active_tax_rates.filter(tax_type=tax_type)
        if rates.exists():
            rate = rates.first()  # Get first (lowest rate) for this type
            tax_class_rate_map[tax_type] = {
                "rate_id": rate.id,
                "percentage": float(rate.rate_percentage),
                "name": rate.name,
            }

    context = {
        "page_title": f"Line Items - {invoice.invoice_number}",
        "invoice": invoice,
        "line_items": line_items,
        "products": Product.objects.filter(is_active=True),
        "tax_rates": active_tax_rates,
        "tax_class_rate_map": json.dumps(tax_class_rate_map),
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Invoices", "invoices:list")
            .add(
                f"Invoice: {invoice.invoice_number}",
                "invoices:detail",
                {"pk": invoice.id},
            )
            .add_current("Line Items")
            .build()
        ),
    }
    return render(request, "6_invoices/invoice_line_items.html", context)


@login_required
@require_http_methods(["POST"])
def add_line_item_view(request, pk):
    """Add line item to invoice via AJAX."""
    from django.http import JsonResponse

    invoice = get_object_or_404(Invoice, pk=pk, is_active=True, status="draft")

    try:
        # Get form data with detailed logging
        print(f"[add_line_item_view] POST data keys: {list(request.POST.keys())}")

        product_id = request.POST.get("product", "").strip()
        description = request.POST.get("description", "").strip()
        quantity_str = request.POST.get("quantity", "0").strip()
        unit_price_str = request.POST.get("unit_price", "0").strip()
        tax_rate_str = request.POST.get("tax_rate", "0").strip()

        print(
            f"[add_line_item_view] Raw values: product={repr(product_id)}, qty={repr(quantity_str)}, price={repr(unit_price_str)}, tax={repr(tax_rate_str)}"
        )

        # Convert to float with error handling
        try:
            quantity = float(quantity_str) if quantity_str else 0
            unit_price = float(unit_price_str) if unit_price_str else 0
            tax_rate = float(tax_rate_str) if tax_rate_str else 0
        except (ValueError, TypeError) as e:
            print(f"[add_line_item_view] Parse error: {e}")
            print(
                f"[add_line_item_view] Tried to parse: qty={repr(quantity_str)}, price={repr(unit_price_str)}, tax={repr(tax_rate_str)}"
            )
            return JsonResponse(
                {"success": False, "error": "Invalid numeric values provided"},
                status=400,
            )

        print(
            f"[add_line_item_view] Parsed values: qty={quantity}, price={unit_price}, tax={tax_rate}"
        )

        # Validate required fields
        if not description and not product_id:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Please provide a description or select a product",
                },
                status=400,
            )

        if quantity <= 0:
            return JsonResponse(
                {"success": False, "error": "Quantity must be greater than 0"},
                status=400,
            )

        if unit_price < 0:
            return JsonResponse(
                {"success": False, "error": "Unit price cannot be negative"}, status=400
            )

        # Get product if selected
        product = None
        if product_id:
            product = get_object_or_404(Product, pk=product_id, is_active=True)
            description = description or product.name

        # Get TaxRate instance from percentage
        from decimal import Decimal

        try:
            tax_rate_decimal = Decimal(str(tax_rate))
            tax_rate_obj = TaxRate.objects.get(rate_percentage=tax_rate_decimal)
        except TaxRate.DoesNotExist:
            available_rates = TaxRate.objects.all().values_list(
                "rate_percentage", flat=True
            )
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Tax rate {tax_rate}% not found. Available rates: {list(available_rates)}",
                },
                status=400,
            )

        # Calculate line_amount, tax_amount, and line_total
        from decimal import Decimal as Dec

        quantity_dec = Dec(str(quantity))
        unit_price_dec = Dec(str(unit_price))
        line_amount = quantity_dec * unit_price_dec
        tax_amount = line_amount * (tax_rate_obj.rate_percentage / 100)
        line_total = line_amount + tax_amount

        # Check if identical line item already exists (consolidation)
        # Match on: product, description, unit_price, and tax_rate
        existing_item = InvoiceLineItem.objects.filter(
            invoice=invoice,
            product=product,
            description=description,
            unit_price=unit_price_dec,
            tax_rate=tax_rate_obj,
        ).first()

        if existing_item:
            # Update existing item's quantity and recalculate its totals
            existing_item.quantity = existing_item.quantity + quantity_dec
            existing_item.line_amount = (
                existing_item.quantity * existing_item.unit_price
            )
            existing_item.tax_amount = existing_item.line_amount * (
                existing_item.tax_rate.rate_percentage / 100
            )
            existing_item.line_total = (
                existing_item.line_amount + existing_item.tax_amount
            )
            existing_item.save()
            line_item = existing_item
            print(
                f"[add_line_item_view] Consolidated: Updated existing item {line_item.id} quantity to {line_item.quantity}"
            )
        else:
            # Create new line item
            line_item = InvoiceLineItem.objects.create(
                invoice=invoice,
                product=product,
                description=description,
                quantity=quantity_dec,
                unit_price=unit_price_dec,
                line_amount=line_amount,
                tax_rate=tax_rate_obj,
                tax_amount=tax_amount,
                line_total=line_total,
            )
            print(f"[add_line_item_view] Created new line item {line_item.id}")

        # Recalculate invoice totals from all line items
        from django.db.models import Sum
        from decimal import Decimal as Dec

        line_items = invoice.line_items.all()
        invoice.subtotal_amount = line_items.aggregate(Sum("line_amount"))[
            "line_amount__sum"
        ] or Dec("0")
        invoice.vat_amount = line_items.aggregate(Sum("tax_amount"))[
            "tax_amount__sum"
        ] or Dec("0")
        invoice.total_amount = line_items.aggregate(Sum("line_total"))[
            "line_total__sum"
        ] or Dec("0")
        invoice.amount_due = invoice.total_amount - invoice.amount_paid
        invoice.save()

        return JsonResponse(
            {
                "success": True,
                "message": "Line item added successfully",
                "line_item": {
                    "id": line_item.id,
                    "description": line_item.description,
                    "quantity": line_item.quantity,
                    "unit_price": float(line_item.unit_price),
                    "tax_rate": float(line_item.tax_rate.rate_percentage),
                    "line_total": float(line_item.line_total),
                },
                "invoice_totals": {
                    "subtotal": float(invoice.subtotal_amount),
                    "tax_total": float(invoice.vat_amount),
                    "total": float(invoice.total_amount),
                    "balance_due": float(invoice.amount_due),
                },
            }
        )

    except ValueError as e:
        print(f"[add_line_item_view] ValueError caught: {e}")
        import traceback

        traceback.print_exc()
        return JsonResponse(
            {"success": False, "error": f"Invalid numeric values provided: {str(e)}"},
            status=400,
        )
    except Exception as e:
        print(f"[add_line_item_view] Unexpected error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return JsonResponse(
            {"success": False, "error": f"Error adding line item: {str(e)}"}, status=500
        )


@login_required
@require_http_methods(["POST"])
def edit_line_item_view(request, pk, line_item_id):
    """Edit line item in invoice via AJAX."""
    from django.http import JsonResponse
    from decimal import Decimal as Dec

    invoice = get_object_or_404(Invoice, pk=pk, is_active=True, status="draft")
    line_item = get_object_or_404(InvoiceLineItem, pk=line_item_id, invoice=invoice)

    try:
        # Get form data
        description = request.POST.get("description", "").strip()
        quantity_str = request.POST.get("quantity", "0").strip()
        unit_price_str = request.POST.get("unit_price", "0").strip()
        tax_rate_str = request.POST.get("tax_rate", "0").strip()

        # Convert to appropriate types
        try:
            quantity = float(quantity_str) if quantity_str else 0
            unit_price = float(unit_price_str) if unit_price_str else 0
            tax_rate = float(tax_rate_str) if tax_rate_str else 0
        except (ValueError, TypeError):
            return JsonResponse(
                {"success": False, "error": "Invalid numeric values provided"},
                status=400,
            )

        # Validate required fields
        if not description:
            return JsonResponse(
                {"success": False, "error": "Description is required"}, status=400
            )

        if quantity <= 0:
            return JsonResponse(
                {"success": False, "error": "Quantity must be greater than 0"},
                status=400,
            )

        if unit_price < 0:
            return JsonResponse(
                {"success": False, "error": "Unit price cannot be negative"}, status=400
            )

        # Get TaxRate instance from percentage
        try:
            tax_rate_decimal = Dec(str(tax_rate))
            tax_rate_obj = TaxRate.objects.get(rate_percentage=tax_rate_decimal)
        except TaxRate.DoesNotExist:
            TaxRate.objects.all().values_list("rate_percentage", flat=True)
            return JsonResponse(
                {"success": False, "error": f"Tax rate {tax_rate}% not found"},
                status=400,
            )

        # Calculate totals
        quantity_dec = Dec(str(quantity))
        unit_price_dec = Dec(str(unit_price))
        line_amount = quantity_dec * unit_price_dec
        tax_amount = line_amount * (tax_rate_obj.rate_percentage / 100)
        line_total = line_amount + tax_amount

        # Update line item
        line_item.description = description
        line_item.quantity = quantity_dec
        line_item.unit_price = unit_price_dec
        line_item.tax_rate = tax_rate_obj
        line_item.line_amount = line_amount
        line_item.tax_amount = tax_amount
        line_item.line_total = line_total
        line_item.save()

        # Recalculate invoice totals
        line_items = invoice.line_items.all()
        invoice.subtotal_amount = line_items.aggregate(Sum("line_amount"))[
            "line_amount__sum"
        ] or Dec("0")
        invoice.vat_amount = line_items.aggregate(Sum("tax_amount"))[
            "tax_amount__sum"
        ] or Dec("0")
        invoice.total_amount = line_items.aggregate(Sum("line_total"))[
            "line_total__sum"
        ] or Dec("0")
        invoice.amount_due = invoice.total_amount - invoice.amount_paid
        invoice.save()

        return JsonResponse(
            {
                "success": True,
                "message": "Line item updated successfully",
                "line_item": {
                    "id": line_item.id,
                    "description": line_item.description,
                    "quantity": float(line_item.quantity),
                    "unit_price": float(line_item.unit_price),
                    "tax_rate": float(line_item.tax_rate.rate_percentage),
                    "tax_amount": float(line_item.tax_amount),
                    "line_total": float(line_item.line_total),
                },
                "invoice_totals": {
                    "subtotal": float(invoice.subtotal_amount),
                    "tax_total": float(invoice.vat_amount),
                    "total": float(invoice.total_amount),
                    "balance_due": float(invoice.amount_due),
                },
            }
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        return JsonResponse(
            {"success": False, "error": f"Error updating line item: {str(e)}"},
            status=500,
        )


@login_required
@require_http_methods(["POST", "DELETE"])
def remove_line_item_view(request, pk, line_item_id):
    """Remove line item from invoice via AJAX."""
    from django.http import JsonResponse
    from decimal import Decimal as Dec

    invoice = get_object_or_404(Invoice, pk=pk, is_active=True, status="draft")
    line_item = get_object_or_404(InvoiceLineItem, pk=line_item_id, invoice=invoice)

    try:
        line_item.delete()

        # Recalculate invoice totals
        line_items = invoice.line_items.all()
        invoice.subtotal_amount = line_items.aggregate(Sum("line_amount"))[
            "line_amount__sum"
        ] or Dec("0")
        invoice.vat_amount = line_items.aggregate(Sum("tax_amount"))[
            "tax_amount__sum"
        ] or Dec("0")
        invoice.total_amount = line_items.aggregate(Sum("line_total"))[
            "line_total__sum"
        ] or Dec("0")
        invoice.amount_due = invoice.total_amount - invoice.amount_paid
        invoice.save()

        return JsonResponse(
            {
                "success": True,
                "message": "Line item removed successfully",
                "invoice_totals": {
                    "subtotal": float(invoice.subtotal_amount),
                    "tax_total": float(invoice.vat_amount),
                    "total": float(invoice.total_amount),
                    "balance_due": float(invoice.amount_due),
                },
            }
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        return JsonResponse(
            {"success": False, "error": f"Error removing line item: {str(e)}"},
            status=500,
        )


@login_required
def invoice_history_view(request, pk):
    """View invoice history from audit log."""
    invoice = get_object_or_404(Invoice, pk=pk, is_active=True)

    history = (
        AuditLog.objects.filter(entity_type="invoice", entity_id=pk)
        .select_related("actor")
        .order_by("-timestamp")
    )

    context = {
        "page_title": f"History - {invoice.invoice_number}",
        "invoice": invoice,
        "history": history,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Invoices", "invoices:list")
            .add(
                f"Invoice: {invoice.invoice_number}",
                "invoices:detail",
                {"pk": invoice.id},
            )
            .add_current("History")
            .build()
        ),
    }
    return render(request, "6_invoices/invoice_history.html", context)


@login_required
@role_required("Admin", "Accountant")
@require_http_methods(["POST"])
def invoices_delete_view(request, pk):
    """Soft delete invoice (draft only)."""
    from django.contrib import messages

    invoice = get_object_or_404(Invoice, pk=pk, status="draft")
    number = invoice.invoice_number
    invoice.is_active = False
    invoice.save()
    messages.success(request, f"Invoice {number} deleted!")
    return redirect("invoices:list")


@login_required
def invoices_outstanding_view(request):
    """List outstanding (unpaid/partially paid) invoices."""
    queryset = (
        Invoice.objects.filter(is_active=True, status__in=["issued", "overdue"])
        .select_related("client")
        .order_by("-invoice_date")
    )

    # Filtering
    search = request.GET.get("search", "")
    if search:
        queryset = queryset.filter(
            Q(invoice_number__icontains=search) | Q(client__name__icontains=search)
        )

    client = request.GET.get("client")
    if client:
        queryset = queryset.filter(client_id=client)

    # Pagination
    invoices = paginate_queryset(request, queryset, per_page=20)
    clients = Client.objects.filter(is_active=True).order_by("name")

    context = {
        "page_title": "Outstanding Invoices",
        "invoices": invoices,
        "clients": clients,
        "search": search,
        "selected_client": client,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Invoices", "invoices:list")
            .add_current("Outstanding")
            .build()
        ),
    }
    return render(request, "6_invoices/invoices_outstanding.html", context)


@login_required
def invoices_pdf_view(request, pk):
    """Generate and serve PDF for invoice (download)."""
    from django.http import HttpResponse
    from invoicing_app.notifications.pdf_service import PDFService
    from django.core.files.storage import default_storage
    from django.contrib import messages

    invoice = get_object_or_404(Invoice, pk=pk)

    try:
        # Generate/retrieve PDF (checks for existing cached PDF first)
        pdf_path = PDFService.generate_invoice_pdf(invoice.id, save=True)

        # Open and return the file for download
        with default_storage.open(pdf_path, "rb") as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
            )

        logger.info(f"Served invoice PDF {invoice.invoice_number} for download")
        return response
    except Exception as e:
        logger.error(f"Error serving PDF for invoice {pk}: {str(e)}")
        messages.error(request, f"Error serving PDF: {str(e)}")
        return redirect("invoices_detail", pk=pk)


@login_required
def invoices_print_view(request, pk):
    """Open invoice PDF in new tab for printing."""
    from django.http import HttpResponse
    from invoicing_app.notifications.pdf_service import PDFService
    from django.core.files.storage import default_storage
    from django.contrib import messages

    invoice = get_object_or_404(Invoice, pk=pk)

    try:
        # Generate/retrieve PDF (checks for existing cached PDF first)
        pdf_path = PDFService.generate_invoice_pdf(invoice.id, save=True)

        # Open and return the file inline for printing
        with default_storage.open(pdf_path, "rb") as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type="application/pdf")
            response["Content-Disposition"] = (
                f'inline; filename="invoice_{invoice.invoice_number}.pdf"'
            )

        logger.info(f"Opened invoice PDF {invoice.invoice_number} for printing")
        return response
    except Exception as e:
        logger.error(f"Error generating PDF for invoice {pk}: {str(e)}")
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect("invoices_detail", pk=pk)


@login_required
def invoices_display_pdf_view(request, pk):
    """Display invoice as formatted HTML PDF page (view in browser)."""
    import qrcode
    from io import BytesIO
    import base64

    invoice = get_object_or_404(Invoice, pk=pk)

    try:
        # Get company settings for logo and company info
        try:
            company_settings = CompanySettings.objects.get()
        except CompanySettings.DoesNotExist:
            company_settings = None

        # Get company logo if available
        company_logo = None
        if company_settings and company_settings.company_logo:
            company_logo = company_settings.company_logo.url

        # Generate QR code that contains invoice details
        qr_content_lines = [
            f"Invoice: {invoice.invoice_number}",
            f"Date: {invoice.invoice_date.strftime('%d/%m/%Y')}",
            f"Due: {invoice.due_date.strftime('%d/%m/%Y')}",
            f"Client: {invoice.client.name}",
            f"Total: KES {invoice.total_amount:.2f}",
        ]

        if company_settings and company_settings.tax_id:
            qr_content_lines.append(f"Tax ID: {company_settings.tax_id}")

        qr_content = "\n".join(qr_content_lines)

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)

        # Convert QR code to image
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64 data URI
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        qr_data = base64.b64encode(qr_buffer.getvalue()).decode()
        qr_data_uri = f"data:image/png;base64,{qr_data}"

        # Prepare context with company information
        context = {
            "invoice": invoice,
            "line_items": invoice.line_items.all(),
            "company_name": company_settings.company_name if company_settings else "",
            "company_address": (
                company_settings.company_address if company_settings else ""
            ),
            "company_phone": company_settings.company_phone if company_settings else "",
            "company_email": company_settings.company_email if company_settings else "",
            "company_logo": company_logo,
            "company_tax_id": company_settings.tax_id if company_settings else "",
            "invoice_qr_code": qr_data_uri,
            # Bank Details
            "bank_account_name": (
                company_settings.bank_account_name if company_settings else ""
            ),
            "bank_account_number": (
                company_settings.bank_account_number if company_settings else ""
            ),
            "bank_name": company_settings.bank_name if company_settings else "",
            "bank_branch": company_settings.bank_branch if company_settings else "",
            "bank_swift_code": (
                company_settings.bank_swift_code if company_settings else ""
            ),
            "bank_iban": company_settings.bank_iban if company_settings else "",
            # M-Pesa Details
            "mpesa_paybill_number": (
                company_settings.mpesa_paybill_number if company_settings else ""
            ),
            "mpesa_account_name": (
                company_settings.mpesa_account_name if company_settings else ""
            ),
            "mpesa_phone": company_settings.mpesa_phone if company_settings else "",
        }

        logger.info(f"Rendered PDF display for invoice {invoice.invoice_number}")
        return render(request, "invoicing_app/invoices/invoice_pdf.html", context)
    except Exception as e:
        logger.error(f"Error rendering PDF display for invoice {pk}: {str(e)}")
        messages.error(request, f"Error generating PDF display: {str(e)}")
        return redirect("invoices:detail", pk=pk)


@login_required
def invoices_view_pdf_view(request):
    """Generate PDF for list view (invoices_view.html)."""
    from django.http import HttpResponse
    from invoicing_app.notifications.pdf_service import PDFService

    try:
        # Get filters and sort parameters
        sort = request.GET.get("sort", "invoice_number")
        client = request.GET.get("client")
        status = request.GET.get("status")

        # Build queryset
        invoices = Invoice.objects.filter(is_active=True).select_related(
            "client", "created_by"
        )

        if client:
            invoices = invoices.filter(client__id=client)
        if status:
            invoices = invoices.filter(status=status)

        invoices = invoices.order_by(sort)

        context = {
            "invoices": invoices,
            "title": "Invoices List",
        }

        # Generate PDF (returns bytes)
        pdf_content = PDFService.generate_report_pdf(
            "invoices_list",
            context,
            "6_invoices/invoices_view_pdf.html",
            "invoices_list",
        )

        # Serve PDF directly from bytes
        response = HttpResponse(pdf_content, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="invoices_list.pdf"'

        logger.info("Served invoices list PDF for download")
        return response
    except Exception as e:
        logger.error(f"Error generating invoices list PDF: {str(e)}")
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect("invoices:list")


@login_required
def invoices_send_view(request, pk):
    """Send invoice to client via email with PDF attachment."""
    from django.http import JsonResponse
    from invoicing_app.notifications.email_service import email_service
    from invoicing_app.notifications.pdf_service import pdf_service

    invoice = get_object_or_404(Invoice, pk=pk)

    if request.method == "POST":
        try:
            # Generate PDF for invoice
            pdf_content = pdf_service.generate_invoice_pdf(invoice.id, save=False)

            # Send email with PDF attachment
            success = email_service.send_invoice_issued_notification(
                client_email=invoice.client.email,
                client_name=invoice.client.name,
                invoice_number=invoice.invoice_number,
                invoice_date=invoice.invoice_date.strftime("%B %d, %Y"),
                total_amount=f"{invoice.currency} {invoice.total_amount:,.2f}",
                due_date=invoice.due_date.strftime("%B %d, %Y"),
                pdf_content=(
                    pdf_content.getvalue()
                    if hasattr(pdf_content, "getvalue")
                    else pdf_content
                ),
            )

            if success:
                # Update invoice status
                invoice.status = "sent"
                invoice.sent_at = timezone.now()
                invoice.updated_by = request.user
                invoice.save()

                # Return JSON response
                return JsonResponse(
                    {
                        "success": True,
                        "message": f"Invoice {invoice.invoice_number} sent successfully to {invoice.client.email}!",
                    }
                )
            else:
                return JsonResponse(
                    {
                        "success": False,
                        "message": f"Failed to send invoice {invoice.invoice_number}. Please try again.",
                    }
                )

        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Error sending invoice: {str(e)}"}
            )

    context = {
        "invoice": invoice,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Invoices", "invoices:list")
            .add(
                f"Invoice: {invoice.invoice_number}",
                "invoices:detail",
                {"pk": invoice.id},
            )
            .add_current("Send Email")
            .build()
        ),
    }
    return render(request, "6_invoices/invoice_issue_confirm.html", context)


@login_required
def invoice_cancel_confirm_view(request, pk):
    """Confirm invoice cancellation."""
    from django.contrib import messages

    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == "POST":
        invoice.status = "cancelled"
        invoice.cancelled_at = timezone.now()
        invoice.updated_by = request.user
        invoice.save()
        messages.success(request, f"Invoice {invoice.invoice_number} cancelled!")
        return redirect("invoices:list")
    context = {
        "invoice": invoice,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Invoices", "invoices:list")
            .add(
                f"Invoice: {invoice.invoice_number}",
                "invoices:detail",
                {"pk": invoice.id},
            )
            .add_current("Confirm Cancel")
            .build()
        ),
    }
    return render(request, "6_invoices/invoice_cancel_confirm.html", context)


@login_required
def invoice_mark_paid_view(request, pk):
    """Mark invoice as paid."""
    from django.contrib import messages

    invoice = get_object_or_404(Invoice, pk=pk, is_active=True)

    if request.method == "POST":
        # Mark invoice as paid
        invoice.status = "paid"
        invoice.paid_at = timezone.now()
        invoice.amount_paid = invoice.total_amount
        invoice.amount_due = 0
        invoice.updated_by = request.user
        invoice.save()

        messages.success(request, f"Invoice {invoice.invoice_number} marked as paid!")
        return redirect("invoices:detail", pk=invoice.id)

    context = {
        "invoice": invoice,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Invoices", "invoices:list")
            .add(
                f"Invoice: {invoice.invoice_number}",
                "invoices:detail",
                {"pk": invoice.id},
            )
            .add_current("Mark Paid")
            .build()
        ),
    }
    return render(request, "6_invoices/invoice_mark_paid_confirm.html", context)


@login_required
def invoice_clone_view(request, pk):
    """Clone existing invoice with new ID and reset status to draft."""
    from django.contrib import messages
    from invoicing_app.invoices.services import InvoiceNumberService

    original_invoice = get_object_or_404(Invoice, pk=pk, is_active=True)

    if request.method == "POST":
        try:
            # Get invoice prefix from company settings
            try:
                settings = CompanySettings.objects.get()
                prefix = settings.invoice_prefix
            except CompanySettings.DoesNotExist:
                prefix = "INV"

            # Generate new invoice number
            new_invoice_number = InvoiceNumberService.generate_next_number(
                prefix=prefix
            )

            # Create new invoice as draft
            cloned_invoice = Invoice.objects.create(
                invoice_number=new_invoice_number,
                client=original_invoice.client,
                invoice_date=timezone.now().date(),
                due_date=request.POST.get("due_date")
                or (timezone.now().date() + timedelta(days=30)),
                description=original_invoice.description,
                currency=original_invoice.currency,
                status="draft",
                created_by=request.user,
                updated_by=request.user,
            )

            # Clone all line items
            for line_item in original_invoice.line_items.all():
                InvoiceLineItem.objects.create(
                    invoice=cloned_invoice,
                    product=line_item.product,
                    description=line_item.description,
                    quantity=line_item.quantity,
                    unit_price=line_item.unit_price,
                    tax_rate=line_item.tax_rate,
                    line_amount=line_item.line_amount,
                    tax_amount=line_item.tax_amount,
                    line_total=line_item.line_total,
                )

            # Recalculate totals
            from django.db.models import Sum

            line_items = cloned_invoice.line_items.all()
            cloned_invoice.subtotal_amount = (
                line_items.aggregate(Sum("line_amount"))["line_amount__sum"] or 0
            )
            cloned_invoice.vat_amount = (
                line_items.aggregate(Sum("tax_amount"))["tax_amount__sum"] or 0
            )
            cloned_invoice.total_amount = (
                line_items.aggregate(Sum("line_total"))["line_total__sum"] or 0
            )
            cloned_invoice.amount_due = cloned_invoice.total_amount
            cloned_invoice.save()

            messages.success(
                request,
                f"Invoice {new_invoice_number} created from {original_invoice.invoice_number}!",
            )
            return redirect("invoices:detail", pk=cloned_invoice.id)

        except Exception as e:
            messages.error(request, f"Error cloning invoice: {str(e)}")
            return redirect("invoices:detail", pk=original_invoice.id)

    context = {
        "page_title": f"Clone Invoice - {original_invoice.invoice_number}",
        "invoice": original_invoice,
        "default_due_date": (timezone.now().date() + timedelta(days=30)).isoformat(),
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Invoices", "invoices:list")
            .add(
                f"Invoice: {original_invoice.invoice_number}",
                "invoices:detail",
                {"pk": original_invoice.id},
            )
            .add_current("Clone")
            .build()
        ),
    }
    return render(request, "6_invoices/invoice_clone.html", context)
