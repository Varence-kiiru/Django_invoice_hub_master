"""
Payment management HTML views.
Provides CRUD operations and reconciliation for payments.
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum
from django.utils import timezone

from invoicing_app.payments.models import Payment, PaymentMethod
from invoicing_app.invoices.models import Invoice
from invoicing_app.core.breadcrumb_config import BreadcrumbBuilder

logger = logging.getLogger(__name__)


# ━━━━━ UTILITY FUNCTIONS ━━━━━


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


def reconcile_payment(payment):
    """Reconcile a payment and update invoice status."""
    from invoicing_app.payments.models import PaymentReconciliation
    from decimal import Decimal
    from django.db.models import Sum

    # Create reconciliation record
    PaymentReconciliation.objects.create(
        payment=payment,
        invoice=payment.invoice,
        amount_matched=payment.amount,
        reconciled_by=payment.recorded_by,
        notes=f"Auto-reconciled payment {payment.transaction_reference or 'N/A'}",
    )

    # Recalculate invoice amounts from all confirmed payments
    invoice = payment.invoice
    invoice.refresh_from_db()  # Get latest state

    # Calculate total paid from all confirmed payments
    total_paid = invoice.payments.filter(status="confirmed").aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    # Update invoice paid and due amounts
    invoice.amount_paid = total_paid
    invoice.amount_due = invoice.total_amount - total_paid

    # Update invoice status based on remaining balance
    if invoice.amount_due <= 0:
        invoice.status = "paid"
        invoice.paid_at = payment.payment_date
    elif invoice.amount_due < invoice.total_amount:
        invoice.status = "partial"
    elif invoice.amount_due > 0 and invoice.due_date < timezone.now().date():
        invoice.status = "overdue"
    else:
        invoice.status = "issued"  # Keep as issued if not overdue yet

    invoice.save(
        update_fields=["amount_paid", "amount_due", "status", "paid_at", "updated_at"]
    )
    return invoice


def confirm_payment_view(request, pk):
    """Confirm a pending payment."""
    payment = get_object_or_404(Payment, pk=pk, status="pending")
    payment.status = "confirmed"
    payment.save()

    # Reconcile the payment
    reconcile_payment(payment)

    messages.success(
        request, f"Payment {payment.transaction_reference or payment.id} confirmed!"
    )
    return redirect("payments:detail", pk=pk)


def reverse_payment_view(request, pk):
    """Reverse a confirmed payment."""
    payment = get_object_or_404(Payment, pk=pk, status="confirmed")
    payment.status = "reversed"
    payment.save()

    # Update invoice status back to issued/partial
    invoice = payment.invoice
    if invoice.amount_due > 0:
        invoice.status = (
            "issued" if invoice.amount_due == invoice.total_amount else "partial"
        )
        invoice.paid_date = None
        invoice.save()

    messages.success(
        request, f"Payment {payment.transaction_reference or payment.id} reversed!"
    )
    return redirect("payments:detail", pk=pk)


# ━━━━━ PAYMENT MANAGEMENT VIEWS ━━━━━


@login_required
def payments_list_view(request):
    """List all payments with pagination and advanced filtering."""
    from invoicing_app.core.models import CompanySettings
    from invoicing_app.core.search_filters import (
        AdvancedFilterBuilder,
        FullTextSearch,
        parse_url_filters,
    )
    from invoicing_app.core.models import SavedFilter

    # Check if payments feature is enabled
    settings = CompanySettings.get_settings()
    if not settings.enable_payments:
        messages.error(
            request, "Payment tracking is currently disabled by your administrator"
        )
        return redirect("core:dashboard")

    queryset = Payment.objects.select_related(
        "invoice", "invoice__client", "payment_method"
    )

    # Parse URL filters
    criteria = parse_url_filters(request.GET)

    # Apply advanced filters
    if criteria:
        queryset = AdvancedFilterBuilder.apply_payment_filters(queryset, criteria)

    # Apply full-text search
    search_query = request.GET.get("q", "")
    if search_query:
        queryset = FullTextSearch.search_payments(queryset, search_query)

    # Legacy search parameter support
    legacy_search = request.GET.get("search", "")
    if legacy_search and not search_query:
        queryset = FullTextSearch.search_payments(queryset, legacy_search)
        search_query = legacy_search

    # Get user's saved filters
    user_filters = SavedFilter.get_user_filters(request.user, "payment")

    # Pagination
    payments = paginate_queryset(
        request, queryset.order_by("-payment_date"), per_page=20
    )

    context = {
        "page_title": "Payments",
        "payments": payments,
        "search_query": search_query,
        "current_filters": criteria,
        "user_filters": user_filters,
        "status_list": request.GET.getlist("status"),
        "method_list": request.GET.getlist("method"),
        "client_name": request.GET.get("client_name", ""),
        "invoice_number": request.GET.get("invoice_number", ""),
        "min_amount": request.GET.get("min_amount", ""),
        "max_amount": request.GET.get("max_amount", ""),
        "from_date": request.GET.get("from_date", ""),
        "to_date": request.GET.get("to_date", ""),
        "status_choices": Payment.STATUS_CHOICES,
        "breadcrumbs": (BreadcrumbBuilder().add_home().add_current("Payments").build()),
    }
    return render(request, "7_payments/payments_list.html", context)


@login_required
def payments_create_view(request):
    """Record new payment."""
    from invoicing_app.core.models import CompanySettings

    # Check if payments feature is enabled
    settings = CompanySettings.get_settings()
    if not settings.enable_payments:
        messages.error(
            request, "Payment tracking is currently disabled by your administrator"
        )
        return redirect("core:dashboard")

    # Check if this is being called from an invoice detail page
    invoice_id_param = request.GET.get("invoice")
    pre_selected_invoice = None

    if invoice_id_param:
        try:
            pre_selected_invoice = Invoice.objects.get(
                id=invoice_id_param, is_active=True
            )
        except Invoice.DoesNotExist:
            pass

    if request.method == "POST":
        try:
            from invoicing_app.core.models import CompanySettings
            from .services import PaymentReceiptNumberService

            invoice_id = request.POST.get("invoice")
            amount = float(request.POST.get("amount"))
            payment_method_id = request.POST.get("payment_method")

            # Validate invoice exists and is payable
            try:
                invoice = Invoice.objects.get(
                    id=invoice_id,
                    is_active=True,
                    amount_due__gt=0,
                    status__in=["issued", "sent", "viewed", "overdue", "partial"],
                )
            except Invoice.DoesNotExist:
                messages.error(
                    request,
                    "Selected invoice is not available for payment. Only issued, sent, viewed, overdue, or partially paid invoices can receive payments.",
                )
                return redirect("payments:create")

            # Check if payment amount exceeds invoice balance
            if amount > invoice.amount_due:
                messages.error(
                    request,
                    f"Payment amount cannot exceed invoice balance of {invoice.amount_due}",
                )
                return redirect("payments:create")

            # Get payment prefix from settings
            settings = CompanySettings.get_settings()
            receipt_number = PaymentReceiptNumberService.generate_next_number(
                prefix=settings.payment_prefix
            )

            # Create payment with confirmed status for immediate reconciliation
            payment = Payment.objects.create(
                receipt_number=receipt_number,
                invoice=invoice,
                amount=amount,
                payment_method_id=payment_method_id,
                payment_date=request.POST.get("payment_date") or timezone.now().date(),
                transaction_reference=request.POST.get("reference", "").strip(),
                notes=request.POST.get("notes", "").strip(),
                recorded_by=request.user,
                status="confirmed",  # Set to confirmed immediately
            )

            # Reconcile payment and update invoice status
            reconcile_payment(payment)

            messages.success(
                request, f"Payment of {payment.amount} recorded and reconciled!"
            )
            return redirect("payments:detail", pk=payment.id)
        except ValueError:
            messages.error(request, "Invalid payment amount.")
        except Exception as e:
            messages.error(request, f"Error recording payment: {str(e)}")

    # Get payable invoices - any with outstanding balance (issued, sent, viewed, overdue, or partially paid)
    # Draft invoices are NOT payable and should not appear in the dropdown
    payable_invoices = Invoice.objects.filter(
        is_active=True,
        amount_due__gt=0,
        status__in=["issued", "sent", "viewed", "overdue", "partial"],
    ).order_by("-invoice_date")

    context = {
        "page_title": "Record Payment",
        "invoices": payable_invoices,
        "pre_selected_invoice": pre_selected_invoice,
        "payment_methods": PaymentMethod.objects.filter(is_active=True),
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Payments", "payments:list")
            .add_current("New Payment")
            .build()
        ),
    }
    return render(request, "7_payments/payments_create.html", context)


@login_required
def payments_detail_view(request, pk):
    """View payment details."""
    from invoicing_app.core.models import CompanySettings

    # Check if payments feature is enabled
    settings = CompanySettings.get_settings()
    if not settings.enable_payments:
        messages.error(
            request, "Payment tracking is currently disabled by your administrator"
        )
        return redirect("core:dashboard")

    payment = get_object_or_404(Payment, pk=pk)

    # Calculate total payments for the invoice
    total_payments = (
        payment.invoice.payments.aggregate(total=Sum("amount"))["total"] or 0
    )

    context = {
        "page_title": f"Payment #{pk}",
        "payment": payment,
        "total_payments": total_payments,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Payments", "payments:list")
            .add_current(f"Payment: {payment.receipt_number}")
            .build()
        ),
    }
    return render(request, "7_payments/payments_detail.html", context)


@login_required
def payments_edit_view(request, pk):
    """Edit payment."""
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == "POST":
        messages.success(request, "Payment updated!")
        return redirect("payments:detail", pk=pk)
    context = {
        "payment": payment,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Payments", "payments:list")
            .add(
                f"Payment: {payment.receipt_number}",
                "payments:detail",
                {"pk": payment.id},
            )
            .add_current("Edit")
            .build()
        ),
    }
    return render(request, "7_payments/payments_edit.html", context)


@login_required
@require_http_methods(["POST"])
def payments_delete_view(request, pk):
    """Delete payment."""
    payment = get_object_or_404(Payment, pk=pk)
    payment.delete()
    messages.success(request, "Payment deleted!")
    return redirect("payments:list")


@login_required
def payment_reconciliation_view(request):
    """Bank reconciliation view."""
    payments = Payment.objects.filter(status="pending").select_related(
        "invoice__client", "payment_method"
    )

    context = {
        "page_title": "Payment Reconciliation",
        "pending_payments": payments,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Payments", "payments:list")
            .add_current("Reconciliation")
            .build()
        ),
    }
    return render(request, "7_payments/payment_reconciliation.html", context)


@login_required
def payment_matching_view(request, pk):
    """Match payment to invoices."""
    payment = get_object_or_404(Payment, pk=pk)
    context = {
        "page_title": "Match Payment",
        "payment": payment,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Payments", "payments:list")
            .add(
                f"Payment: {payment.receipt_number}",
                "payments:detail",
                {"pk": payment.id},
            )
            .add_current("Match Payment")
            .build()
        ),
    }
    return render(request, "7_payments/payment_matching.html", context)


@login_required
def payment_receipt_view(request, pk):
    """Generate/view payment receipt."""
    import base64
    import qrcode
    from io import BytesIO
    from invoicing_app.core.models import CompanySettings

    payment = get_object_or_404(Payment, pk=pk)

    # Calculate previous payments (all payments for this invoice except this one)
    previous_payments = (
        payment.invoice.payments.exclude(id=payment.id).aggregate(total=Sum("amount"))[
            "total"
        ]
        or 0
    )

    # Get company settings
    company_settings = CompanySettings.get_settings()

    # Generate QR code with payment information
    qr_content_lines = [
        f"Payment Receipt: {payment.receipt_number or payment.id}",
        f"Invoice: {payment.invoice.invoice_number}",
        f"Amount: {payment.invoice.currency} {payment.amount:.2f}",
        f"Date: {payment.payment_date.strftime('%Y-%m-%d')}",
        f"Method: {payment.payment_method.name}",
    ]

    if payment.transaction_reference:
        qr_content_lines.append(f"Reference: {payment.transaction_reference}")

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

    # Get company information
    company_logo = None
    company_name = company_settings.company_name if company_settings else ""
    company_address = company_settings.company_address if company_settings else ""
    company_phone = company_settings.company_phone if company_settings else ""
    company_email = company_settings.company_email if company_settings else ""
    company_tax_id = company_settings.tax_id if company_settings else ""

    if company_settings and company_settings.company_logo:
        company_logo = company_settings.company_logo.url

    context = {
        "page_title": f"Receipt - Payment #{pk}",
        "payment": payment,
        "previous_payments": previous_payments,
        "receipt_qr_code": qr_data_uri,
        "company_name": company_name,
        "company_address": company_address,
        "company_phone": company_phone,
        "company_email": company_email,
        "company_logo": company_logo,
        "company_tax_id": company_tax_id,
        "company_settings": company_settings,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Payments", "payments:list")
            .add_current("Payment Receipt")
            .build()
        ),
    }
    return render(request, "7_payments/payment_receipt.html", context)


@login_required
def payment_receipt_pdf_view(request, pk):
    """Download payment receipt PDF - reuses existing or generates new."""
    from invoicing_app.notifications.pdf_service import PDFService
    from django.core.files.storage import default_storage
    from django.http import HttpResponse

    payment = get_object_or_404(Payment, pk=pk)

    try:
        # Generate/retrieve PDF (checks for existing first)
        pdf_path = PDFService.generate_payment_receipt_pdf(payment.id, save=True)

        # Open and return the file
        with default_storage.open(pdf_path, "rb") as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="receipt_{payment.receipt_number or payment.id}.pdf"'
            )

        return response

    except Exception as e:
        messages.error(request, f"Error retrieving receipt PDF: {str(e)}")
        return redirect("payments:detail", pk=pk)


@login_required
def payment_receipt_print_view(request, pk):
    """Open payment receipt PDF for printing - reuses existing or generates new."""
    from invoicing_app.notifications.pdf_service import PDFService
    from django.core.files.storage import default_storage
    from django.http import HttpResponse

    payment = get_object_or_404(Payment, pk=pk)

    try:
        # Generate/retrieve PDF (checks for existing first)
        pdf_path = PDFService.generate_payment_receipt_pdf(payment.id, save=True)

        # Open and return the file inline
        with default_storage.open(pdf_path, "rb") as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type="application/pdf")
            response["Content-Disposition"] = (
                f'inline; filename="receipt_{payment.receipt_number or payment.id}.pdf"'
            )
            response["X-PDF-Action"] = "print"

        return response

    except Exception as e:
        messages.error(request, f"Error generating receipt PDF: {str(e)}")
        return redirect("payments:detail", pk=pk)


@login_required
def payment_receipt_download_view(request, pk):
    """Download payment receipt PDF."""
    from invoicing_app.notifications.pdf_service import PDFService
    from django.http import HttpResponse

    payment = get_object_or_404(Payment, pk=pk)

    try:
        # Generate PDF (returns bytes directly)
        pdf_content = PDFService.generate_payment_receipt_pdf(payment.id, save=False)

        # Serve PDF directly from bytes
        response = HttpResponse(pdf_content, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="receipt_{payment.receipt_number or payment.id}.pdf"'
        )

        logger.info(
            f"Served payment receipt PDF {payment.receipt_number or payment.id} for download"
        )
        return response

    except Exception as e:
        logger.error(f"Error generating payment receipt PDF: {str(e)}")
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect("payments:detail", pk=pk)


# ━━━━━ PAYMENT METHODS MANAGEMENT VIEWS ━━━━━


@login_required
def payment_methods_list_view(request):
    """List all payment methods."""

    payment_methods = PaymentMethod.objects.all().order_by("-created_at")

    context = {
        "page_title": "Payment Methods",
        "payment_methods": payment_methods,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Payments", "payments:list")
            .add_current("Payment Methods")
            .build()
        ),
    }
    return render(request, "7_payments/payment_methods_list.html", context)


@login_required
def payment_method_create_view(request):
    """Create new payment method."""
    from invoicing_app.payments.forms import PaymentMethodForm

    if request.method == "POST":
        form = PaymentMethodForm(request.POST)
        if form.is_valid():
            payment_method = form.save(commit=False)
            payment_method.created_by = request.user
            payment_method.updated_by = request.user
            payment_method.save()
            messages.success(
                request, f'Payment method "{payment_method.name}" created!'
            )
            return redirect("payments:methods-list")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PaymentMethodForm()

    context = {
        "page_title": "Create Payment Method",
        "form": form,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Payments", "payments:list")
            .add("Payment Methods", "payments:methods-list")
            .add_current("New Payment Method")
            .build()
        ),
    }
    return render(request, "7_payments/payment_methods_form.html", context)


@login_required
def payment_method_edit_view(request, pk):
    """Edit existing payment method."""
    from invoicing_app.payments.forms import PaymentMethodForm

    payment_method = get_object_or_404(PaymentMethod, pk=pk)

    if request.method == "POST":
        form = PaymentMethodForm(request.POST, instance=payment_method)
        if form.is_valid():
            payment_method = form.save(commit=False)
            payment_method.updated_by = request.user
            payment_method.save()
            messages.success(
                request, f'Payment method "{payment_method.name}" updated!'
            )
            return redirect("payments:methods-list")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PaymentMethodForm(instance=payment_method)

    context = {
        "page_title": f"Edit Payment Method - {payment_method.name}",
        "form": form,
        "payment_method": payment_method,
        "is_edit": True,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Payments", "payments:list")
            .add("Payment Methods", "payments:methods-list")
            .add_current(f"Edit - {payment_method.name}")
            .build()
        ),
    }
    return render(request, "7_payments/payment_methods_form.html", context)


@login_required
@require_http_methods(["POST"])
def payment_method_delete_view(request, pk):
    """Delete payment method."""

    payment_method = get_object_or_404(PaymentMethod, pk=pk)
    name = payment_method.name

    # Check if method is in use
    if Payment.objects.filter(payment_method=payment_method).exists():
        messages.error(
            request,
            f'Cannot delete "{name}" - it is in use by payments. Mark as inactive instead.',
        )
        return redirect("payments:methods-list")

    payment_method.delete()
    messages.success(request, f'Payment method "{name}" deleted!')
    return redirect("payments:methods-list")
