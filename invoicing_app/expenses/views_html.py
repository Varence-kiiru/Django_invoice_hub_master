"""
Expense management HTML views for dashboard and user interface.
Provides CRUD operations, filtering, and reporting for expense tracking.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime

from invoicing_app.expenses.models import (
    Expense,
    ExpenseCategory,
    Vendor,
)
from invoicing_app.expenses.forms import ExpenseForm, VendorForm, ExpenseCategoryForm
from invoicing_app.core.permissions import user_has_permission
from invoicing_app.core.breadcrumb_config import BreadcrumbBuilder


# ==================== PERMISSION HELPERS ====================
def get_user_role(user):
    """
    Safely get user's role object from invoicing_profile.
    Returns: UserRole object or None
    """
    try:
        if user.is_superuser:
            # Superusers get admin equivalent
            from invoicing_app.user_management.models import UserRole

            admin_role = UserRole.objects.filter(name="admin").first()
            return admin_role
        return (
            user.invoicing_profile.role if hasattr(user, "invoicing_profile") else None
        )
    except (AttributeError, ObjectDoesNotExist):
        return None


def get_user_role_name(user):
    """
    Safely get user's role name as string.
    Returns: 'admin', 'manager', 'staff', 'user', or None
    """
    role = get_user_role(user)
    return role.name if role else None


def is_admin(user):
    """Check if user is admin (full system access)"""
    return user.is_superuser or get_user_role_name(user) == "admin"


def is_manager(user):
    """Check if user is manager or above"""
    role = get_user_role(user)
    if not role:
        return False
    return is_admin(user) or role.is_at_least("manager")


def is_staff(user):
    """Check if user is staff or above"""
    role = get_user_role(user)
    if not role:
        return False
    return is_admin(user) or role.is_at_least("staff")


def can_create_expense(user):
    """Check if user has permission to create expenses"""
    return user_has_permission(user, "create_expenses")


def can_view_expense(user, expense):
    """
    Check if user can view this expense.
    Based on permission system and ownership.
    """
    # Check view_all_expenses first (admin/manager)
    if user_has_permission(user, "view_all_expenses"):
        return True
    # Check view_own_expenses
    if user_has_permission(user, "view_own_expenses"):
        return expense.submitted_by == user
    return False


def can_edit_expense(user, expense):
    """
    Check if user can edit this expense.
    Based on permission system and expense status/ownership.
    """
    # Check edit_any_expense (admin only)
    if user_has_permission(user, "edit_any_expense"):
        return True

    # Check edit_own_expenses (manager level)
    if user_has_permission(user, "edit_own_expenses"):
        if expense.status in ["draft", "submitted"]:
            return expense.submitted_by == user
        return False

    # Check edit_own_draft_expenses (staff)
    if user_has_permission(user, "edit_own_draft_expenses"):
        if expense.status != "draft":
            return False
        return expense.submitted_by == user

    return False


def can_delete_expense(user, expense):
    """
    Check if user can delete this expense.
    Based on permission system and expense status.
    """
    # Check delete_any_expense (admin only)
    if user_has_permission(user, "delete_any_expense"):
        return expense.status == "draft"

    # Check delete_own_expenses (manager level)
    if user_has_permission(user, "delete_own_expenses"):
        if expense.status != "draft":
            return False
        return expense.submitted_by == user

    # Check delete_own_draft_expenses (staff)
    if user_has_permission(user, "delete_own_draft_expenses"):
        if expense.status != "draft":
            return False
        return expense.submitted_by == user

    return False


def can_approve_expense(user):
    """Check if user has permission to approve/reject/mark paid expenses"""
    return user_has_permission(user, "approve_expenses")


@login_required
def expenses_list_view(request):
    """
    List all expenses with search, filtering, and pagination.
    Displays expense information, status, amount, and category breakdown.
    Respects permission-based visibility.
    """
    # Apply view filtering based on permissions
    if user_has_permission(request.user, "view_all_expenses"):
        expenses_qs = Expense.objects.all()  # View all
    elif user_has_permission(request.user, "view_own_expenses"):
        # View only their own
        expenses_qs = Expense.objects.filter(submitted_by=request.user)
    else:
        # No permission to view expenses
        messages.error(request, "You do not have permission to view expenses.")
        return redirect("dashboard")

    expenses_qs = expenses_qs.select_related(
        "category", "vendor", "submitted_by", "approved_by"
    )

    # Search functionality
    search_query = request.GET.get("search", "")
    if search_query:
        expenses_qs = expenses_qs.filter(
            Q(description__icontains=search_query)
            | Q(reference_number__icontains=search_query)
            | Q(vendor__name__icontains=search_query)
        )

    # Filter by status
    status_filter = request.GET.get("status", "")
    if status_filter and status_filter in [
        "draft",
        "submitted",
        "approved",
        "rejected",
        "paid",
    ]:
        expenses_qs = expenses_qs.filter(status=status_filter)

    # Filter by category
    category_filter = request.GET.get("category", "")
    if category_filter:
        try:
            category = ExpenseCategory.objects.get(pk=category_filter)
            expenses_qs = expenses_qs.filter(category=category)
        except ExpenseCategory.DoesNotExist:
            pass

    # Filter by vendor
    vendor_filter = request.GET.get("vendor", "")
    if vendor_filter:
        try:
            vendor = Vendor.objects.get(pk=vendor_filter)
            expenses_qs = expenses_qs.filter(vendor=vendor)
        except Vendor.DoesNotExist:
            pass

    # Filter by date range
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            expenses_qs = expenses_qs.filter(expense_date__gte=start_date_obj)
        except ValueError:
            pass
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            expenses_qs = expenses_qs.filter(expense_date__lte=end_date_obj)
        except ValueError:
            pass

    # Order by date descending
    expenses_qs = expenses_qs.order_by("-expense_date", "-created_at")

    # Calculate totals and metrics
    total_amount = expenses_qs.aggregate(Sum("amount"))["amount__sum"] or 0
    by_status = (
        expenses_qs.values("status")
        .annotate(count=Count("id"), total=Sum("amount"))
        .order_by("status")
    )
    by_category = (
        expenses_qs.values("category__name")
        .annotate(count=Count("id"), total=Sum("amount"))
        .order_by("-total")
    )

    # Pagination
    paginator = Paginator(expenses_qs, 25)
    page_number = request.GET.get("page", 1)
    expenses = paginator.get_page(page_number)

    # Get filter options
    categories = ExpenseCategory.objects.filter(is_active=True)
    vendors = Vendor.objects.filter(is_active=True)

    context = {
        "expenses": expenses,
        "page_obj": expenses,
        "search_query": search_query,
        "status_filter": status_filter,
        "category_filter": category_filter,
        "vendor_filter": vendor_filter,
        "start_date": start_date,
        "end_date": end_date,
        "total_amount": total_amount,
        "by_status": by_status,
        "by_category": by_category,
        "categories": categories,
        "vendors": vendors,
        "all_statuses": ["draft", "submitted", "approved", "rejected", "paid"],
        "breadcrumbs": (BreadcrumbBuilder().add_home().add_current("Expenses").build()),
    }
    return render(request, "11_expenses/expenses_list.html", context)


@login_required
def expenses_create_view(request):
    """
    Create a new expense with form validation.
    Only admin, manager, and staff can create expenses.
    Handles expense details, receipt uploads, and approvals.
    """
    # Check if user can create expenses
    if not can_create_expense(request.user):
        messages.error(request, "You do not have permission to create expenses.")
        return redirect("expenses:list")

    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                expense = form.save(commit=False)
                expense.submitted_by = request.user
                expense.status = "draft"  # Start as draft
                expense.save()
                messages.success(
                    request, f'Expense "{expense.description}" created successfully.'
                )
                return redirect("expenses:detail", pk=expense.id)
            except Exception as e:
                messages.error(request, f"Error creating expense: {str(e)}")
    else:
        form = ExpenseForm()

    context = {
        "form": form,
        "page_title": "Create New Expense",
        "action": "Create",
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Expenses", "expenses:list")
            .add_current("New Expense")
            .build()
        ),
    }
    return render(request, "11_expenses/expenses_form.html", context)


@login_required
def expenses_detail_view(request, pk):
    """
    Display expense details with approval workflow.
    Shows all expense information, status, and approval chain.
    Respects role-based access.
    """
    expense = get_object_or_404(Expense, pk=pk)

    # Check if user can view this expense
    if not can_view_expense(request.user, expense):
        messages.error(request, "You do not have permission to view this expense.")
        return redirect("expenses:list")

    # Get approval history if available
    approval_history = []
    if expense.approved_date:
        approval_history.append(
            {
                "status": "Approved",
                "user": expense.approved_by,
                "date": expense.approved_date,
            }
        )

    context = {
        "expense": expense,
        "approval_history": approval_history,
        "page_title": f"Expense: {expense.description}",
        "can_edit": can_edit_expense(request.user, expense),
        "can_delete": can_delete_expense(request.user, expense),
        "can_approve": can_approve_expense(request.user)
        and expense.status == "submitted",
        "can_reject": can_approve_expense(request.user)
        and expense.status == "submitted",
        "can_pay": can_approve_expense(request.user) and expense.status == "approved",
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Expenses", "expenses:list")
            .add_current(f"Expense #{expense.id}")
            .build()
        ),
    }
    return render(request, "11_expenses/expenses_detail.html", context)


@login_required
def expenses_edit_view(request, pk):
    """
    Edit an existing expense.
    Admin: can edit any expense
    Accountant/User: can only edit their own draft expenses
    """
    expense = get_object_or_404(Expense, pk=pk)

    # Check if user can edit this expense
    if not can_edit_expense(request.user, expense):
        if expense.status != "draft":
            messages.error(request, "You can only edit draft expenses.")
        else:
            messages.error(request, "You can only edit your own expenses.")
        return redirect("expenses:detail", pk=expense.id)

    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            try:
                expense = form.save()
                messages.success(
                    request, f'Expense "{expense.description}" updated successfully.'
                )
                return redirect("expenses:detail", pk=expense.id)
            except Exception as e:
                messages.error(request, f"Error updating expense: {str(e)}")
    else:
        form = ExpenseForm(instance=expense)

    context = {
        "form": form,
        "expense": expense,
        "page_title": f"Edit: {expense.description}",
        "action": "Edit",
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Expenses", "expenses:list")
            .add(f"Expense #{expense.id}", "expenses:detail", {"pk": expense.id})
            .add_current("Edit")
            .build()
        ),
    }
    return render(request, "11_expenses/expenses_form.html", context)


@login_required
def expenses_delete_view(request, pk):
    """
    Delete an expense.
    Admin: can delete any draft
    Accountant/User: can only delete their own drafts
    """
    expense = get_object_or_404(Expense, pk=pk)

    # Check if user can delete this expense
    if not can_delete_expense(request.user, expense):
        if expense.status != "draft":
            messages.error(request, "You can only delete draft expenses.")
        else:
            messages.error(request, "You can only delete your own expenses.")
        return redirect("expenses:detail", pk=expense.id)

    if request.method == "POST":
        try:
            description = expense.description
            expense.delete()
            messages.success(request, f'Expense "{description}" has been deleted.')
            return redirect("expenses:list")
        except Exception as e:
            messages.error(request, f"Error deleting expense: {str(e)}")

    context = {
        "expense": expense,
        "page_title": f"Delete: {expense.description}",
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Expenses", "expenses:list")
            .add(f"Expense #{expense.id}", "expenses:detail", {"pk": expense.id})
            .add_current("Delete")
            .build()
        ),
    }
    return render(request, "11_expenses/expenses_delete_confirm.html", context)


@login_required
def vendors_list_view(request):
    """
    List all vendors with search and filtering.
    """
    vendors_qs = Vendor.objects.all()

    # Search functionality
    search_query = request.GET.get("search", "")
    if search_query:
        vendors_qs = vendors_qs.filter(
            Q(name__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(phone__icontains=search_query)
        )

    # Filter by status
    status_filter = request.GET.get("status", "")
    if status_filter:
        vendors_qs = vendors_qs.filter(is_active=(status_filter == "active"))

    # Annotate with expense count
    vendors_qs = vendors_qs.annotate(
        expense_count=Count("expenses"), total_spent=Sum("expenses__amount")
    ).order_by("-created_at")

    # Pagination
    paginator = Paginator(vendors_qs, 25)
    page_number = request.GET.get("page", 1)
    vendors = paginator.get_page(page_number)

    context = {
        "vendors": vendors,
        "page_obj": vendors,
        "search_query": search_query,
        "status_filter": status_filter,
        "page_title": "Vendors",
        "breadcrumbs": (BreadcrumbBuilder().add_home().add_current("Vendors").build()),
    }
    return render(request, "11_expenses/vendors_list.html", context)


@login_required
def vendors_create_view(request):
    """
    Create a new vendor.
    """
    if request.method == "POST":
        form = VendorForm(request.POST)
        if form.is_valid():
            try:
                vendor = form.save()
                messages.success(
                    request, f'Vendor "{vendor.name}" created successfully.'
                )
                return redirect("expenses:vendors-detail", pk=vendor.id)
            except Exception as e:
                messages.error(request, f"Error creating vendor: {str(e)}")
    else:
        form = VendorForm()

    context = {
        "form": form,
        "page_title": "Create New Vendor",
        "action": "Create",
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Vendors", "expenses:vendors-list")
            .add_current("New Vendor")
            .build()
        ),
    }
    return render(request, "11_expenses/vendors_form.html", context)


@login_required
def vendors_detail_view(request, pk):
    """
    Display vendor details and related expenses.
    """
    vendor = get_object_or_404(Vendor, pk=pk)

    # Get related expenses
    expenses = vendor.expenses.all().order_by("-expense_date")
    total_spent = expenses.aggregate(Sum("amount"))["amount__sum"] or 0

    context = {
        "vendor": vendor,
        "expenses": expenses[:10],  # Last 10 expenses
        "total_spent": total_spent,
        "page_title": f"Vendor: {vendor.name}",
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Vendors", "expenses:vendors-list")
            .add_current(f"Vendor #{vendor.id}")
            .build()
        ),
    }
    return render(request, "11_expenses/vendors_detail.html", context)


@login_required
def vendors_edit_view(request, pk):
    """
    Edit an existing vendor.
    """
    vendor = get_object_or_404(Vendor, pk=pk)

    if request.method == "POST":
        form = VendorForm(request.POST, instance=vendor)
        if form.is_valid():
            try:
                vendor = form.save()
                messages.success(
                    request, f'Vendor "{vendor.name}" updated successfully.'
                )
                return redirect("expenses:vendors-detail", pk=vendor.id)
            except Exception as e:
                messages.error(request, f"Error updating vendor: {str(e)}")
    else:
        form = VendorForm(instance=vendor)

    context = {
        "form": form,
        "vendor": vendor,
        "page_title": f"Edit: {vendor.name}",
        "action": "Edit",
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Vendors", "expenses:vendors-list")
            .add(f"Vendor #{vendor.id}", "expenses:vendors-detail", {"pk": vendor.id})
            .add_current("Edit")
            .build()
        ),
    }
    return render(request, "11_expenses/vendors_form.html", context)


@login_required
def vendors_delete_view(request, pk):
    """
    Delete a vendor (with confirmation).
    """
    vendor = get_object_or_404(Vendor, pk=pk)

    if request.method == "POST":
        try:
            vendor_name = vendor.name
            vendor.delete()
            messages.success(request, f'Vendor "{vendor_name}" has been deleted.')
            return redirect("expenses:vendors-list")
        except Exception as e:
            messages.error(request, f"Error deleting vendor: {str(e)}")

    context = {
        "vendor": vendor,
        "page_title": f"Delete: {vendor.name}",
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Vendors", "expenses:vendors-list")
            .add(f"Vendor #{vendor.id}", "expenses:vendors-detail", {"pk": vendor.id})
            .add_current("Delete")
            .build()
        ),
    }
    return render(request, "11_expenses/vendors_delete_confirm.html", context)


@login_required
def categories_list_view(request):
    """
    List all expense categories with expense counts.
    """
    categories_qs = ExpenseCategory.objects.all()

    # Annotate with expense count
    categories_qs = categories_qs.annotate(
        expense_count=Count("expenses"), total_spent=Sum("expenses__amount")
    ).order_by("name")

    context = {
        "categories": categories_qs,
        "page_title": "Expense Categories",
        "breadcrumbs": (
            BreadcrumbBuilder().add_home().add_current("Categories").build()
        ),
    }
    return render(request, "11_expenses/categories_list.html", context)


@login_required
def categories_create_view(request):
    """
    Create a new expense category.
    """
    if request.method == "POST":
        form = ExpenseCategoryForm(request.POST)
        if form.is_valid():
            try:
                category = form.save()
                messages.success(
                    request, f'Category "{category.name}" created successfully.'
                )
                return redirect("expenses:categories-list")
            except Exception as e:
                messages.error(request, f"Error creating category: {str(e)}")
    else:
        form = ExpenseCategoryForm()

    context = {
        "form": form,
        "page_title": "Create New Category",
        "action": "Create",
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Categories", "expenses:categories-list")
            .add_current("New Category")
            .build()
        ),
    }
    return render(request, "11_expenses/categories_form.html", context)


@login_required
def categories_edit_view(request, pk):
    """
    Edit an existing expense category.
    """
    category = get_object_or_404(ExpenseCategory, pk=pk)

    if request.method == "POST":
        form = ExpenseCategoryForm(request.POST, instance=category)
        if form.is_valid():
            try:
                category = form.save()
                messages.success(
                    request, f'Category "{category.name}" updated successfully.'
                )
                return redirect("expenses:categories-list")
            except Exception as e:
                messages.error(request, f"Error updating category: {str(e)}")
    else:
        form = ExpenseCategoryForm(instance=category)

    context = {
        "form": form,
        "category": category,
        "page_title": f"Edit: {category.name}",
        "action": "Edit",
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Categories", "expenses:categories-list")
            .add(f"Category #{category.id}", None)
            .add_current("Edit")
            .build()
        ),
    }
    return render(request, "11_expenses/categories_form.html", context)


@login_required
def categories_delete_view(request, pk):
    """
    Delete an expense category (with confirmation).
    """
    category = get_object_or_404(ExpenseCategory, pk=pk)

    if request.method == "POST":
        try:
            category_name = category.name
            category.delete()
            messages.success(request, f'Category "{category_name}" has been deleted.')
            return redirect("expenses:categories-list")
        except Exception as e:
            messages.error(request, f"Error deleting category: {str(e)}")

    context = {
        "category": category,
        "page_title": f"Delete: {category.name}",
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Categories", "expenses:categories-list")
            .add_current("Delete")
            .build()
        ),
    }
    return render(request, "11_expenses/categories_delete_confirm.html", context)


# ━━━ Expense Approval Workflow ━━━


@login_required
@require_http_methods(["POST"])
def expenses_submit_view(request, pk):
    """
    Submit an expense for approval (change status from draft to submitted).
    Users can only submit their own expenses if they have permission.
    """
    expense = get_object_or_404(Expense, pk=pk)

    # Check if user has permission to submit expenses
    if not user_has_permission(request.user, "submit_expenses"):
        messages.error(request, "You do not have permission to submit expenses.")
        return redirect("expenses:list")

    # Check if user can submit this expense (must be their own)
    if expense.submitted_by != request.user and not user_has_permission(
        request.user, "edit_any_expense"
    ):
        messages.error(request, "You can only submit your own expenses.")
        return redirect("expenses:list")

    if expense.status != "draft":
        messages.error(request, "Only draft expenses can be submitted.")
        return redirect("expenses:detail", pk=expense.id)

    try:
        expense.status = "submitted"
        expense.submitted_date = timezone.now().date()
        expense.save()
        messages.success(
            request, f'Expense "{expense.description}" submitted for approval.'
        )
    except Exception as e:
        messages.error(request, f"Error submitting expense: {str(e)}")

    return redirect("expenses:detail", pk=expense.id)


@login_required
@require_http_methods(["POST"])
def expenses_approve_view(request, pk):
    """
    Approve an expense (change status from submitted to approved).
    Only admin and accountant roles can approve.
    """
    expense = get_object_or_404(Expense, pk=pk)

    # Check permission - only admin/accountant can approve
    if not can_approve_expense(request.user):
        messages.error(request, "You do not have permission to approve expenses.")
        return redirect("expenses:detail", pk=expense.id)

    if expense.status != "submitted":
        messages.error(request, "Only submitted expenses can be approved.")
        return redirect("expenses:detail", pk=expense.id)

    try:
        expense.status = "approved"
        expense.approved_date = timezone.now().date()
        expense.approved_by = request.user
        expense.save()
        messages.success(request, f'Expense "{expense.description}" approved.')
    except Exception as e:
        messages.error(request, f"Error approving expense: {str(e)}")

    return redirect("expenses:detail", pk=expense.id)


@login_required
@require_http_methods(["POST"])
def expenses_reject_view(request, pk):
    """
    Reject an expense (change status from submitted to rejected).
    Only admin and accountant roles can reject.
    """
    expense = get_object_or_404(Expense, pk=pk)

    # Check permission
    if not can_approve_expense(request.user):
        messages.error(request, "You do not have permission to reject expenses.")
        return redirect("expenses:detail", pk=expense.id)

    if expense.status != "submitted":
        messages.error(request, "Only submitted expenses can be rejected.")
        return redirect("expenses:detail", pk=expense.id)

    try:
        expense.status = "rejected"
        expense.save()
        messages.success(request, f'Expense "{expense.description}" rejected.')
    except Exception as e:
        messages.error(request, f"Error rejecting expense: {str(e)}")

    return redirect("expenses:detail", pk=expense.id)


@login_required
@require_http_methods(["POST"])
def expenses_mark_paid_view(request, pk):
    """
    Mark an expense as paid (change status from approved to paid).
    Only admin and accountant roles can mark as paid.
    """
    expense = get_object_or_404(Expense, pk=pk)

    # Check permission
    if not can_approve_expense(request.user):
        messages.error(request, "You do not have permission to mark expenses as paid.")
        return redirect("expenses:detail", pk=expense.id)

    if expense.status != "approved":
        messages.error(request, "Only approved expenses can be marked as paid.")
        return redirect("expenses:detail", pk=expense.id)

    try:
        expense.status = "paid"
        expense.paid_date = timezone.now().date()
        expense.save()
        messages.success(request, f'Expense "{expense.description}" marked as paid.')
    except Exception as e:
        messages.error(request, f"Error marking expense as paid: {str(e)}")

    return redirect("expenses:detail", pk=expense.id)
