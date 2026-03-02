"""
Product/service management HTML views for Week 3 implementation.
Provides CRUD operations for product catalog.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum

from invoicing_app.products.models import Product, ProductCategory
from invoicing_app.products.forms import ProductForm
from invoicing_app.invoices.models import InvoiceLineItem
from invoicing_app.core.views_html import role_required


@login_required
def products_list_view(request):
    """
    List all products/services with search, filter, and pagination.
    Shows product details, pricing, usage count, and availability.
    """
    products_qs = Product.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products_qs = products_qs.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by category
    category_filter = request.GET.get('category', '')
    if category_filter:
        products_qs = products_qs.filter(category__id=category_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        products_qs = products_qs.filter(is_active=(status_filter == 'active'))
    
    # Annotate with usage metrics
    products_qs = products_qs.annotate(
        usage_count=Count('invoice_lines'),
        revenue=Sum('invoice_lines__line_total')
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products_qs, 25)
    page_number = request.GET.get('page', 1)
    products = paginator.get_page(page_number)
    
    categories = ProductCategory.objects.filter(is_active=True)
    
    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'page_obj': products,
    }
    return render(request, '5_products/products_list.html', context)


@login_required
@role_required('Admin')
def products_create_view(request):
    """
    Create a new product/service with form validation.
    """
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_by = request.user if request.user.is_authenticated else None
            product.save()
            return redirect('products:detail', pk=product.id)
    else:
        form = ProductForm()
    
    context = {'form': form}
    return render(request, '5_products/products_create.html', context)


@login_required
@role_required('Admin')
def products_edit_view(request, pk):
    """
    Edit an existing product's information.
    """
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            return redirect('products:detail', pk=product.id)
    else:
        form = ProductForm(instance=product)
    
    context = {'product': product, 'form': form}
    return render(request, '5_products/products_edit.html', context)


@login_required
def products_detail_view(request, pk):
    """
    View complete product details with usage statistics.
    """
    product = get_object_or_404(Product, pk=pk)
    
    # Get usage metrics
    line_items = InvoiceLineItem.objects.filter(product=product)
    usage_count = line_items.count()
    total_quantity_sold = line_items.aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_revenue = line_items.aggregate(Sum('line_amount'))['line_amount__sum'] or 0
    
    # Recent invoices using this product
    recent_invoices = line_items.select_related('invoice').order_by('-invoice__invoice_date')[:10]
    
    context = {
        'product': product,
        'usage_count': usage_count,
        'total_quantity_sold': total_quantity_sold,
        'total_revenue': total_revenue,
        'recent_invoices': recent_invoices,
    }
    return render(request, '5_products/products_detail.html', context)


@login_required
@role_required('Admin')
@require_http_methods(["GET", "POST"])
def products_delete_view(request, pk):
    """
    Archive/soft-delete a product (don't remove if in use).
    """
    product = get_object_or_404(Product, pk=pk)
    
    # Check if product is in use
    in_use = InvoiceLineItem.objects.filter(product=product).exists()
    
    if request.method == 'POST':
        # Soft delete
        product.is_active = False
        product.save()
        return redirect('products:list')
    
    context = {
        'product': product,
        'in_use': in_use,
        'in_use_count': InvoiceLineItem.objects.filter(product=product).count(),
    }
    return render(request, '5_products/products_delete_confirm.html', context)


@login_required
@role_required('Admin')
def products_import_view(request):
    """
    Bulk import products from CSV file.
    Expected format: sku, name, description, category, unit_price, unit, tax_class
    """
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if csv_file:
            # Parse CSV and validate
            import csv
            failed_rows = []
            success_count = 0
            
            try:
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Create product from CSV data
                        product = Product(
                            sku=row.get('sku', '').strip(),
                            name=row.get('name', '').strip(),
                            description=row.get('description', '').strip(),
                            unit_price=row.get('unit_price', '0'),
                            unit=row.get('unit', 'piece'),
                            created_by=request.user,
                        )
                        
                        # Validate and save
                        product.full_clean()
                        product.save()
                        success_count += 1
                    except Exception as e:
                        failed_rows.append({
                            'row': row_num,
                            'data': row,
                            'error': str(e)
                        })
                
                context = {
                    'success_count': success_count,
                    'failed_rows': failed_rows,
                    'total_rows': reader.line_num -1,
                }
            except Exception as e:
                context = {'error': f'Failed to parse CSV: {str(e)}'}
            
            return render(request, '5_products/products_import_preview.html', context)
    
    return render(request, '5_products/products_import.html')


@login_required
@role_required('Admin')
def products_export_view(request):
    """
    Export products to CSV file.
    """
    import csv
    from django.http import HttpResponse
    
    # Get all active products
    products = Product.objects.filter(is_active=True).select_related('category', 'tax_class')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products_export.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow(['SKU', 'Name', 'Description', 'Category', 'Unit Price', 'Unit', 'Tax Class', 'Status', 'Created Date'])
    
    # Write product rows
    for product in products:
        writer.writerow([
            product.sku,
            product.name,
            product.description or '',
            product.category.name if product.category else '',
            product.unit_price,
            product.get_unit_display(),
            product.tax_class.name if product.tax_class else '',
            'Active' if product.is_active else 'Inactive',
            product.created_at.strftime('%Y-%m-%d') if product.created_at else '',
        ])
    
    return response


@login_required
@role_required('Admin')
def products_bulk_delete_view(request):
    """
    Bulk delete multiple products (soft delete).
    """
    from django.contrib import messages
    
    if request.method == 'POST':
        product_ids = request.POST.getlist('product_ids')
        if product_ids:
            deleted_count = Product.objects.filter(id__in=product_ids, is_active=True).update(is_active=False)
            messages.success(request, f'{deleted_count} product(s) deactivated successfully!')
        else:
            messages.warning(request, 'No products selected.')
    
    return redirect('products:list')


@login_required
@role_required('Admin')
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
        
        return JsonResponse({
            'success': True,
            'is_active': product.is_active,
            'status': 'Active' if product.is_active else 'Inactive'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@role_required('Admin')
def product_categories_view(request):
    """
    Manage product categories.
    """
    categories = ProductCategory.objects.all().annotate(
        product_count=Count('products')
    ).order_by('name')
    
    if request.method == 'POST':
        category_name = request.POST.get('name', '').strip()
        if category_name:
            category, created = ProductCategory.objects.get_or_create(
                name=category_name
            )
            if created:
                return redirect('products:categories')
    
    context = {
        'categories': categories,
    }
    return render(request, '5_products/product_categories.html', context)


@login_required
@role_required('Admin')
def category_delete_view(request, pk):
    """Delete a product category."""
    from django.contrib import messages
    category = get_object_or_404(ProductCategory, pk=pk)
    category.delete()
    messages.success(request, f'Category "{category.name}" deleted successfully!')
    return redirect('products:categories')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAX CLASS MANAGEMENT VIEWS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@login_required
def tax_classes_list_view(request):
    """
    List all tax classes with usage count.
    """
    from invoicing_app.products.models import ProductTaxClass
    
    tax_classes = ProductTaxClass.objects.annotate(
        product_count=Count('products')
    ).order_by('name')
    
    context = {
        'tax_classes': tax_classes,
    }
    # DEPRECATED: Tax class management moved to admin settings (9_admin/settings_tax.html)
    # Redirect to admin settings instead
    from django.shortcuts import redirect
    return redirect('settings-tax')


# Tax Class management has been consolidated into admin settings (9_admin/settings_tax.html)
# These functions are DEPRECATED - tax management is now in core/views_html.py


@login_required
@role_required('Admin')
def category_create_view(request):
    """
    Create a new product category.
    """
    from invoicing_app.products.forms import ProductCategoryForm
    from django.contrib import messages
    
    if request.method == 'POST':
        form = ProductCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('products:categories')
    else:
        form = ProductCategoryForm()
    
    context = {'form': form}
    return render(request, '5_products/category_form.html', context)


@login_required
@role_required('Admin')
def category_edit_view(request, pk):
    """
    Edit an existing product category.
    """
    from invoicing_app.products.forms import ProductCategoryForm
    from django.contrib import messages
    
    category = get_object_or_404(ProductCategory, pk=pk)
    
    if request.method == 'POST':
        form = ProductCategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('products:categories')
    else:
        form = ProductCategoryForm(instance=category)
    
    context = {'form': form, 'category': category}
    return render(request, '5_products/category_form.html', context)
