"""
HTML views for financial tracking frontend.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal

from invoicing_app.organizations.views_billing import get_user_organization
from invoicing_app.core.permissions import (
    can_view_financials,
    can_manage_financials,
)
from invoicing_app.core.breadcrumb_config import BreadcrumbBuilder
from .models import FinancialPeriod, RevenueCollection, TaxLiability
from .forms import TaxLiabilityForm


@login_required
def financial_dashboard(request):
    """Financial dashboard overview."""
    if not can_view_financials(request.user):
        messages.error(request, "You don't have permission to view financial data.")
        return redirect("core:dashboard")

    organization = get_user_organization(request.user)
    if not organization:
        messages.error(request, "No organization found.")
        return redirect("core:dashboard")

    # Current period
    today = timezone.now().date()
    current_period = FinancialPeriod.objects.filter(
        organization=organization,
        start_date__lte=today,
        end_date__gte=today,
    ).first()

    # Financial summary
    total_revenue = RevenueCollection.objects.filter(
        organization=organization
    ).aggregate(total=Sum("revenue_amount"))["total"] or Decimal("0")

    total_tax_collected = RevenueCollection.objects.filter(
        organization=organization
    ).aggregate(total=Sum("tax_amount"))["total"] or Decimal("0")

    pending_tax = TaxLiability.objects.filter(
        organization=organization, status="pending"
    ).aggregate(total=Sum("total_tax_collected"))["total"] or Decimal("0")

    overdue_tax = TaxLiability.objects.filter(
        organization=organization, status="overdue"
    ).aggregate(total=Sum("total_tax_collected"))["total"] or Decimal("0")

    context = {
        "current_period": current_period,
        "total_revenue": total_revenue,
        "total_tax_collected": total_tax_collected,
        "pending_tax": pending_tax,
        "overdue_tax": overdue_tax,
        "can_manage_financials": can_manage_financials(request.user),
        "breadcrumbs": (
            BreadcrumbBuilder().add_home().add_current("Financials").build()
        ),
    }

    return render(request, "15_financials/financial_dashboard.html", context)


@login_required
def financial_periods_list(request):
    """List all financial periods."""
    if not can_view_financials(request.user):
        messages.error(request, "You don't have permission to view financial periods.")
        return redirect("financials:dashboard")

    organization = get_user_organization(request.user)
    if not organization:
        messages.error(request, "No organization found.")
        return redirect("financials:dashboard")

    periods = FinancialPeriod.objects.filter(organization=organization).order_by(
        "-start_date"
    )

    context = {
        "periods": periods,
        "can_manage_financials": can_manage_financials(request.user),
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Financials", "financials:dashboard")
            .add_current("Periods")
            .build()
        ),
    }

    return render(request, "15_financials/financial_periods_list.html", context)


@login_required
def financial_period_detail(request, pk):
    """View financial period details."""
    if not can_view_financials(request.user):
        messages.error(request, "You don't have permission to view financial periods.")
        return redirect("financials:dashboard")

    organization = get_user_organization(request.user)
    if not organization:
        messages.error(request, "No organization found.")
        return redirect("financials:dashboard")

    period = get_object_or_404(FinancialPeriod, pk=pk, organization=organization)

    # Get revenue collections for this period
    revenue_collections = (
        RevenueCollection.objects.filter(financial_period=period)
        .select_related("invoice", "payment")
        .order_by("-collected_date")
    )

    # Get tax liability for this period
    tax_liability = TaxLiability.objects.filter(financial_period=period).first()

    # Calculate period totals
    period_totals = revenue_collections.aggregate(
        total_revenue=Sum("revenue_amount"),
        total_tax=Sum("tax_amount"),
        total_collected=Sum("total_amount"),
    )

    context = {
        "period": period,
        "revenue_collections": revenue_collections,
        "tax_liability": tax_liability,
        "period_totals": period_totals,
        "can_manage_financials": can_manage_financials(request.user),
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Financials", "financials:dashboard")
            .add_section("Periods", "financials:periods-list")
            .add_current(f"Period {period.name}")
            .build()
        ),
    }

    return render(request, "15_financials/financial_period_detail.html", context)


@login_required
def revenue_collections_list(request):
    """List all revenue collections."""
    if not can_view_financials(request.user):
        messages.error(
            request, "You don't have permission to view revenue collections."
        )
        return redirect("financials:dashboard")

    organization = get_user_organization(request.user)
    if not organization:
        messages.error(request, "No organization found.")
        return redirect("financials:dashboard")

    collections = (
        RevenueCollection.objects.filter(organization=organization)
        .select_related("invoice", "payment", "financial_period")
        .order_by("-collected_date")
    )

    context = {
        "collections": collections,
        "can_manage_financials": can_manage_financials(request.user),
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Financials", "financials:dashboard")
            .add_current("Revenue Collections")
            .build()
        ),
    }

    return render(request, "15_financials/revenue_collections_list.html", context)


@login_required
def revenue_collection_detail(request, pk):
    """View revenue collection details."""
    if not can_view_financials(request.user):
        messages.error(
            request, "You don't have permission to view revenue collections."
        )
        return redirect("financials:dashboard")

    organization = get_user_organization(request.user)
    if not organization:
        messages.error(request, "No organization found.")
        return redirect("financials:dashboard")

    collection = get_object_or_404(RevenueCollection, pk=pk, organization=organization)

    # Get related tax liability for this collection
    tax_liability = collection.financial_period.tax_liabilities.filter(
        tax_type=collection.tax_type
    ).first()

    context = {
        "collection": collection,
        "tax_liability": tax_liability,
        "can_manage_financials": can_manage_financials(request.user),
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Financials", "financials:dashboard")
            .add_section("Collections", "financials:revenue-collections-list")
            .add_current(f"Collection #{collection.id}")
            .build()
        ),
    }

    return render(request, "15_financials/revenue_collection_detail.html", context)


@login_required
def tax_liabilities_list(request):
    """List all tax liabilities."""
    if not can_view_financials(request.user):
        messages.error(request, "You don't have permission to view tax liabilities.")
        return redirect("financials:dashboard")

    organization = get_user_organization(request.user)
    if not organization:
        messages.error(request, "No organization found.")
        return redirect("financials:dashboard")

    liabilities = (
        TaxLiability.objects.filter(organization=organization)
        .select_related("financial_period")
        .order_by("-due_date")
    )

    context = {
        "liabilities": liabilities,
        "can_manage_financials": can_manage_financials(request.user),
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Financials", "financials:dashboard")
            .add_current("Tax Liabilities")
            .build()
        ),
    }

    return render(request, "15_financials/tax_liabilities_list.html", context)


@login_required
def tax_liability_detail(request, pk):
    """View tax liability details."""
    if not can_view_financials(request.user):
        messages.error(request, "You don't have permission to view tax liabilities.")
        return redirect("financials:dashboard")

    organization = get_user_organization(request.user)
    if not organization:
        messages.error(request, "No organization found.")
        return redirect("financials:dashboard")

    liability = get_object_or_404(TaxLiability, pk=pk, organization=organization)

    # Get all revenue collections for this period
    collections = (
        RevenueCollection.objects.filter(
            financial_period=liability.financial_period, organization=organization
        )
        .select_related("invoice", "payment")
        .order_by("-collected_date")
    )

    context = {
        "liability": liability,
        "collections": collections,
        "can_manage_financials": can_manage_financials(request.user),
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Financials", "financials:dashboard")
            .add_section("Liabilities", "financials:tax-liabilities-list")
            .add_current(f"Liability #{liability.id}")
            .build()
        ),
    }

    return render(request, "15_financials/tax_liability_detail.html", context)


@login_required
def tax_liability_mark_remitted(request, pk):
    """Mark a tax liability as remitted."""
    if not can_manage_financials(request.user):
        messages.error(request, "You don't have permission to manage tax liabilities.")
        return redirect("financials:tax-liabilities-list")

    organization = get_user_organization(request.user)
    if not organization:
        messages.error(request, "No organization found.")
        return redirect("financials:dashboard")

    liability = get_object_or_404(TaxLiability, pk=pk, organization=organization)

    if request.method == "POST":
        remittance_reference = request.POST.get("remittance_reference", "").strip()
        remitted_date = request.POST.get("remitted_date", "").strip()

        errors = {}
        if not remitted_date:
            errors["remitted_date"] = "Remittance date is required."
        if not remittance_reference:
            errors["remittance_reference"] = (
                "Remittance reference/receipt number is required."
            )

        if not errors:
            try:

                liability.status = "remitted"
                liability.remitted_date = remitted_date
                liability.remittance_reference = remittance_reference
                liability.save()

                # Update all related revenue collections to "remitted"
                RevenueCollection.objects.filter(
                    financial_period=liability.financial_period,
                    organization=organization,
                    tax_type=liability.tax_type,
                ).update(
                    status="remitted",
                    remitted_date=remitted_date,
                    remittance_reference=remittance_reference,
                )

                messages.success(
                    request,
                    f"Tax liability for {liability.financial_period} marked as remitted. "
                    f"Reference: {remittance_reference}",
                )
                return redirect("financials:tax-liability-detail", pk=liability.pk)
            except Exception as e:
                messages.error(request, f"Error marking as remitted: {str(e)}")
        else:
            for error in errors.values():
                messages.error(request, error)

    context = {
        "liability": liability,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Financials", "financials:dashboard")
            .add_section("Liabilities", "financials:tax-liabilities-list")
            .add(
                f"Liability #{liability.id}",
                "financials:tax-liability-detail",
                {"pk": liability.id},
            )
            .add_current("Mark Remitted")
            .build()
        ),
    }
    return render(request, "15_financials/tax_liability_mark_remitted.html", context)


@login_required
def tax_liability_create(request):
    """Create a new tax liability."""
    if not can_manage_financials(request.user):
        messages.error(request, "You don't have permission to manage financials.")
        return redirect("financials:dashboard")

    organization = get_user_organization(request.user)
    if not organization:
        messages.error(request, "No organization found.")
        return redirect("financials:dashboard")

    if request.method == "POST":
        form = TaxLiabilityForm(request.POST)
        if form.is_valid():
            tax_liability = form.save(commit=False)
            tax_liability.organization = organization
            tax_liability.save()
            messages.success(request, "Tax liability created successfully.")
            return redirect("financials:tax-liability-detail", pk=tax_liability.pk)
    else:
        form = TaxLiabilityForm()

    context = {
        "form": form,
        "liability": None,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Financials", "financials:dashboard")
            .add_section("Liabilities", "financials:tax-liabilities-list")
            .add_current("New Liability")
            .build()
        ),
    }
    return render(request, "15_financials/tax_liability_form.html", context)


@login_required
def tax_liability_edit(request, pk):
    """Edit an existing tax liability."""
    if not can_manage_financials(request.user):
        messages.error(request, "You don't have permission to manage financials.")
        return redirect("financials:dashboard")

    organization = get_user_organization(request.user)
    if not organization:
        messages.error(request, "No organization found.")
        return redirect("financials:dashboard")

    liability = get_object_or_404(TaxLiability, pk=pk, organization=organization)

    if request.method == "POST":
        form = TaxLiabilityForm(request.POST, instance=liability)
        if form.is_valid():
            form.save()
            messages.success(request, "Tax liability updated successfully.")
            return redirect("financials:tax-liability-detail", pk=liability.pk)
    else:
        form = TaxLiabilityForm(instance=liability)

    context = {
        "form": form,
        "liability": liability,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Financials", "financials:dashboard")
            .add_section("Liabilities", "financials:tax-liabilities-list")
            .add(
                f"Liability #{liability.id}",
                "financials:tax-liability-detail",
                {"pk": liability.id},
            )
            .add_current("Edit")
            .build()
        ),
    }
    return render(request, "15_financials/tax_liability_form.html", context)
