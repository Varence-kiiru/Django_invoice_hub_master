"""
Product/service management HTML views for Week 3 implementation.
Provides CRUD operations for product catalog.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum

from invoicing_app.products.models import Product, ProductCategory, ProductTaxClass
from invoicing_app.products.forms import ProductForm
from invoicing_app.invoices.models import InvoiceLineItem
from invoicing_app.core.views_html import role_required
from invoicing_app.core.breadcrumb_config import BreadcrumbBuilder


@login_required
def products_list_view(request):
    """
    List all products/services with search, filter, and pagination.
    Shows product details, pricing, usage count, and availability.
    """
    products_qs = Product.objects.all()

    # Search functionality
    search_query = request.GET.get("search", "")
    if search_query:
        products_qs = products_qs.filter(
            Q(name__icontains=search_query)
            | Q(sku__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    # Filter by category
    category_filter = request.GET.get("category", "")
    if category_filter:
        products_qs = products_qs.filter(category__id=category_filter)

    # Filter by status
    status_filter = request.GET.get("status", "")
    if status_filter:
        products_qs = products_qs.filter(is_active=(status_filter == "active"))

    # Annotate with usage metrics
    products_qs = products_qs.annotate(
        usage_count=Count("invoice_lines"), revenue=Sum("invoice_lines__line_total")
    ).order_by("-created_at")

    # Pagination
    paginator = Paginator(products_qs, 25)
    page_number = request.GET.get("page", 1)
    products = paginator.get_page(page_number)

    categories = ProductCategory.objects.filter(is_active=True)

    context = {
        "page_title": "Products",
        "products": products,
        "categories": categories,
        "search_query": search_query,
        "category_filter": category_filter,
        "status_filter": status_filter,
        "page_obj": products,
        "breadcrumbs": (BreadcrumbBuilder().add_home().add_current("Products").build()),
    }
    return render(request, "5_products/products_list.html", context)


@login_required
@role_required("Admin")
def products_create_view(request):
    """
    Create a new product/service with form validation.
    """
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_by = request.user if request.user.is_authenticated else None
            product.save()
            return redirect("products:detail", pk=product.id)
    else:
        form = ProductForm()

    context = {
        "page_title": "New Product",
        "form": form,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Products", "products:list")
            .add_current("New Product")
            .build()
        ),
    }
    return render(request, "5_products/products_create.html", context)


@login_required
@role_required("Admin")
def products_edit_view(request, pk):
    """
    Edit an existing product's information.
    """
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            return redirect("products:detail", pk=product.id)
    else:
        form = ProductForm(instance=product)

    context = {
        "page_title": f"Edit Product: {product.name}",
        "product": product,
        "form": form,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Products", "products:list")
            .add(f"Product: {product.name}", "products:detail", {"pk": product.id})
            .add_current("Edit")
            .build()
        ),
    }
    return render(request, "5_products/products_edit.html", context)


@login_required
def products_detail_view(request, pk):
    """
    View complete product details with usage statistics.
    """
    product = get_object_or_404(Product, pk=pk)

    # Get usage metrics
    line_items = InvoiceLineItem.objects.filter(product=product)
    usage_count = line_items.count()
    total_quantity_sold = line_items.aggregate(Sum("quantity"))["quantity__sum"] or 0
    total_revenue = line_items.aggregate(Sum("line_amount"))["line_amount__sum"] or 0

    # Recent invoices using this product
    recent_invoices = line_items.select_related("invoice").order_by(
        "-invoice__invoice_date"
    )[:10]

    context = {
        "page_title": product.name,
        "product": product,
        "usage_count": usage_count,
        "total_quantity_sold": total_quantity_sold,
        "total_revenue": total_revenue,
        "recent_invoices": recent_invoices,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Products", "products:list")
            .add_current(f"Product: {product.name}")
            .build()
        ),
    }
    return render(request, "5_products/products_detail.html", context)


@login_required
@role_required("Admin")
@require_http_methods(["POST"])
def products_delete_view(request, pk):
    """
    Archive/soft-delete a product (don't remove if in use).
    """
    product = get_object_or_404(Product, pk=pk)
    product.is_active = False
    product.save()
    return redirect("products:list")


@login_required
@role_required("Admin")
def products_import_view(request):
    """
    Bulk import products from CSV file.
    Expected format: sku, name, description, category, unit_price, unit, tax_class
    """
    if request.method == "POST":
        csv_file = request.FILES.get("csv_file")
        if csv_file:
            # Parse CSV and validate
            import csv

            failed_rows = []
            success_count = 0

            try:
                decoded_file = csv_file.read().decode("utf-8").splitlines()
                reader = csv.DictReader(decoded_file)

                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Create product from CSV data
                        product = Product(
                            sku=row.get("sku", "").strip(),
                            name=row.get("name", "").strip(),
                            description=row.get("description", "").strip(),
                            unit_price=row.get("unit_price", "0"),
                            unit=row.get("unit", "piece"),
                            created_by=request.user,
                        )

                        # Validate and save
                        product.full_clean()
                        product.save()
                        success_count += 1
                    except Exception as e:
                        failed_rows.append(
                            {"row": row_num, "data": row, "error": str(e)}
                        )

                context = {
                    "page_title": "Import Results",
                    "success_count": success_count,
                    "failed_rows": failed_rows,
                    "total_rows": reader.line_num - 1,
                    "breadcrumbs": (
                        BreadcrumbBuilder()
                        .add_home()
                        .add_section("Products", "products:list")
                        .add_current("Import Results")
                        .build()
                    ),
                }
            except Exception as e:
                context = {
                    "error": f"Failed to parse CSV: {str(e)}",
                    "breadcrumbs": (
                        BreadcrumbBuilder()
                        .add_home()
                        .add_section("Products", "products:list")
                        .add_current("Import")
                        .build()
                    ),
                }

            return render(request, "5_products/products_import_preview.html", context)

    context = {
        "page_title": "Import Products",
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Products", "products:list")
            .add_current("Import")
            .build()
        ),
    }
    return render(request, "5_products/products_import.html", context)


@login_required
@role_required("Admin")
def products_export_view(request):
    """
    Export products to CSV file.
    """
    import csv
    from django.http import HttpResponse

    # Get all active products
    products = Product.objects.filter(is_active=True).select_related(
        "category", "tax_class"
    )

    # Create CSV response
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="products_export.csv"'

    writer = csv.writer(response)

    # Write header
    writer.writerow(
        [
            "SKU",
            "Name",
            "Description",
            "Category",
            "Unit Price",
            "Unit",
            "Tax Class",
            "Status",
            "Created Date",
        ]
    )

    # Write product rows
    for product in products:
        writer.writerow(
            [
                product.sku,
                product.name,
                product.description or "",
                product.category.name if product.category else "",
                product.unit_price,
                product.get_unit_display(),
                product.tax_class.name if product.tax_class else "",
                "Active" if product.is_active else "Inactive",
                product.created_at.strftime("%Y-%m-%d") if product.created_at else "",
            ]
        )

    return response


@login_required
@role_required("Admin")
def products_bulk_delete_view(request):
    """
    Bulk delete multiple products (soft delete).
    """
    from django.contrib import messages

    if request.method == "POST":
        product_ids = request.POST.getlist("product_ids")
        if product_ids:
            deleted_count = Product.objects.filter(
                id__in=product_ids, is_active=True
            ).update(is_active=False)
            messages.success(
                request, f"{deleted_count} product(s) deactivated successfully!"
            )
        else:
            messages.warning(request, "No products selected.")

    return redirect("products:list")


@login_required
@role_required("Admin")
@require_http_methods(["POST"])
def products_toggle_status_view(request, pk):
    """
    Toggle product active/inactive status via AJAX.
    """
    from django.http import JsonResponse

    try:
        product = get_object_or_404(Product, pk=pk)
        product.is_active = not product.is_active
        product.save()

        return JsonResponse(
            {
                "success": True,
                "is_active": product.is_active,
                "status": "Active" if product.is_active else "Inactive",
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@role_required("Admin")
def product_categories_view(request):
    """
    Manage product categories.
    """
    categories = (
        ProductCategory.objects.all()
        .annotate(product_count=Count("products"))
        .order_by("name")
    )

    if request.method == "POST":
        category_name = request.POST.get("name", "").strip()
        if category_name:
            category, created = ProductCategory.objects.get_or_create(
                name=category_name
            )
            if created:
                return redirect("products:categories")

    context = {
        "page_title": "Categories",
        "categories": categories,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Products", "products:list")
            .add_current("Categories")
            .build()
        ),
    }
    return render(request, "5_products/product_categories.html", context)


@login_required
@role_required("Admin")
@require_http_methods(["POST"])
def category_delete_view(request, pk):
    """Delete a product category."""
    from django.contrib import messages

    category = get_object_or_404(ProductCategory, pk=pk)
    category.delete()
    messages.success(request, f'Category "{category.name}" deleted successfully!')
    return redirect("products:categories")


@login_required
@role_required("Admin")
def category_create_view(request):
    """
    Create a new product category.
    """
    from invoicing_app.products.forms import ProductCategoryForm
    from django.contrib import messages

    if request.method == "POST":
        form = ProductCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(
                request, f'Category "{category.name}" created successfully!'
            )
            return redirect("products:categories")
    else:
        form = ProductCategoryForm()

    context = {
        "page_title": "New Category",
        "form": form,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Products", "products:list")
            .add("Categories", "products:categories")
            .add_current("New Category")
            .build()
        ),
    }
    return render(request, "5_products/category_form.html", context)


@login_required
@role_required("Admin")
def category_edit_view(request, pk):
    """
    Edit an existing product category.
    """
    from invoicing_app.products.forms import ProductCategoryForm
    from django.contrib import messages

    category = get_object_or_404(ProductCategory, pk=pk)

    if request.method == "POST":
        form = ProductCategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(
                request, f'Category "{category.name}" updated successfully!'
            )
            return redirect("products:categories")
    else:
        form = ProductCategoryForm(instance=category)

    context = {
        "page_title": f"Edit Category: {category.name}",
        "form": form,
        "category": category,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Products", "products:list")
            .add("Categories", "products:categories")
            .add_current(f"Edit: {category.name}")
            .build()
        ),
    }
    return render(request, "5_products/category_form.html", context)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAX CLASSES MANAGEMENT VIEWS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@login_required
def tax_classes_list_view(request):
    """
    List all tax classes with filters and usage statistics.
    Shows tax class name, rate type, status, and count of VAT rules.
    """
    from invoicing_app.products.models import ProductTaxClass

    tax_classes_qs = ProductTaxClass.objects.annotate(
        product_count=Count("products"), vat_rule_count=Count("vat_rules")
    )

    # Search functionality
    search_query = request.GET.get("search", "")
    if search_query:
        tax_classes_qs = tax_classes_qs.filter(Q(name__icontains=search_query))

    # Filter by rate type
    rate_type_filter = request.GET.get("rate_type", "")
    if rate_type_filter:
        tax_classes_qs = tax_classes_qs.filter(rate_type=rate_type_filter)

    # Filter by status
    status_filter = request.GET.get("status", "")
    if status_filter:
        tax_classes_qs = tax_classes_qs.filter(is_active=(status_filter == "active"))

    tax_classes_qs = tax_classes_qs.order_by("name")

    # Pagination
    paginator = Paginator(tax_classes_qs, 25)
    page_number = request.GET.get("page", 1)
    tax_classes = paginator.get_page(page_number)

    # Calculate stats
    all_tax_classes = ProductTaxClass.objects.all()
    total_active = all_tax_classes.filter(is_active=True).count()
    total_inactive = all_tax_classes.filter(is_active=False).count()

    context = {
        "page_title": "Tax Classes",
        "tax_classes": tax_classes,
        "page_obj": tax_classes,
        "search_query": search_query,
        "rate_type_filter": rate_type_filter,
        "status_filter": status_filter,
        "total_active": total_active,
        "total_inactive": total_inactive,
        "total_count": all_tax_classes.count(),
        "rate_type_choices": ProductTaxClass.RATE_TYPE_CHOICES,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Products", "products:list")
            .add_current("Tax Classes")
            .build()
        ),
    }
    return render(request, "5_products/tax_classes_list.html", context)


@login_required
@role_required("Admin")
def tax_class_create_view(request):
    """
    Create a new tax class with validation.
    """
    from invoicing_app.products.forms import ProductTaxClassForm
    from django.contrib import messages

    if request.method == "POST":
        form = ProductTaxClassForm(request.POST)
        if form.is_valid():
            tax_class = form.save()
            messages.success(
                request, f'Tax class "{tax_class.name}" created successfully!'
            )
            return redirect("products:tax-class-detail", pk=tax_class.id)
    else:
        form = ProductTaxClassForm()

    context = {
        "page_title": "New Tax Class",
        "form": form,
        "title": "Create Tax Class",
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Products", "products:list")
            .add("Tax Classes", "products:tax-classes-list")
            .add_current("New Tax Class")
            .build()
        ),
    }
    return render(request, "5_products/tax_class_form.html", context)


@login_required
@role_required("Admin")
def tax_class_edit_view(request, pk):
    """
    Edit an existing tax class.
    """
    from invoicing_app.products.forms import ProductTaxClassForm
    from django.contrib import messages

    tax_class = get_object_or_404(ProductTaxClass, pk=pk)

    if request.method == "POST":
        form = ProductTaxClassForm(request.POST, instance=tax_class)
        if form.is_valid():
            tax_class = form.save()
            messages.success(
                request, f'Tax class "{tax_class.name}" updated successfully!'
            )
            return redirect("products:tax-class-detail", pk=tax_class.id)
    else:
        form = ProductTaxClassForm(instance=tax_class)

    context = {
        "page_title": f"Edit Tax Class: {tax_class.name}",
        "form": form,
        "tax_class": tax_class,
        "title": f"Edit Tax Class - {tax_class.name}",
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Products", "products:list")
            .add("Tax Classes", "products:tax-classes-list")
            .add(
                f"Tax Class: {tax_class.name}",
                "products:tax-class-detail",
                {"pk": tax_class.id},
            )
            .add_current("Edit")
            .build()
        ),
    }
    return render(request, "5_products/tax_class_form.html", context)


@login_required
def tax_class_detail_view(request, pk):
    """
    View complete tax class details with related products and VAT rules.
    Shows associated products, VAT rules, and usage statistics.
    """
    from invoicing_app.taxes.models import VATRule

    tax_class = get_object_or_404(ProductTaxClass, pk=pk)

    # Get related data
    products = Product.objects.filter(tax_class=tax_class)
    vat_rules = VATRule.objects.filter(tax_class=tax_class).select_related("tax_rate")

    # Calculate statistics
    product_count = products.count()
    active_products = products.filter(is_active=True).count()
    vat_rule_count = vat_rules.count()
    active_vat_rules = vat_rules.filter(is_active=True).count()

    # Get total usage in invoices
    from invoicing_app.invoices.models import InvoiceLineItem

    invoice_usage = InvoiceLineItem.objects.filter(product__tax_class=tax_class).count()

    context = {
        "page_title": tax_class.name,
        "tax_class": tax_class,
        "products": products,
        "vat_rules": vat_rules,
        "product_count": product_count,
        "active_products": active_products,
        "vat_rule_count": vat_rule_count,
        "active_vat_rules": active_vat_rules,
        "invoice_usage": invoice_usage,
        "breadcrumbs": (
            BreadcrumbBuilder()
            .add_home()
            .add_section("Products", "products:list")
            .add("Tax Classes", "products:tax-classes-list")
            .add_current(f"Tax Class: {tax_class.name}")
            .build()
        ),
    }
    return render(request, "5_products/tax_class_detail.html", context)


@login_required
@role_required("Admin")
@require_http_methods(["POST"])
def tax_class_delete_view(request, pk):
    """
    Archive/soft-delete a tax class (don't remove if in use).
    """
    from django.contrib import messages

    tax_class = get_object_or_404(ProductTaxClass, pk=pk)
    tax_class.is_active = False
    tax_class.save()
    messages.success(request, f'Tax class "{tax_class.name}" deactivated successfully!')
    return redirect("products:tax-classes-list")


@login_required
@role_required("Admin")
@require_http_methods(["POST"])
def tax_class_toggle_status_view(request, pk):
    """
    Toggle tax class active/inactive status via AJAX.
    """
    from django.http import JsonResponse

    try:
        tax_class = get_object_or_404(ProductTaxClass, pk=pk)
        tax_class.is_active = not tax_class.is_active
        tax_class.save()

        return JsonResponse(
            {
                "success": True,
                "is_active": tax_class.is_active,
                "status": "Active" if tax_class.is_active else "Inactive",
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
