"""Views for deliveries management."""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum
from django.utils import timezone

from invoicing_app.deliveries.models import Delivery, DeliveryLineItem
from invoicing_app.invoices.models import Invoice


def get_client_delivery_info(client):
    """
    Extract client's delivery information (name and primary shipping address).
    
    Returns:
        tuple: (recipient_name, delivery_location_str)
    """
    recipient_name = client.name
    
    # Try to get primary shipping address
    shipping_address = client.addresses.filter(
        address_type='shipping',
        is_primary=True
    ).first()
    
    # Fall back to any shipping address
    if not shipping_address:
        shipping_address = client.addresses.filter(
            address_type='shipping'
        ).first()
    
    # Fall back to primary billing address
    if not shipping_address:
        shipping_address = client.addresses.filter(
            address_type='billing',
            is_primary=True
        ).first()
    
    # Fall back to any billing address
    if not shipping_address:
        shipping_address = client.addresses.filter(
            address_type='billing'
        ).first()
    
    # Format address if found
    delivery_location = ''
    if shipping_address:
        address_parts = [
            shipping_address.street_1,
            shipping_address.street_2 or '',
            shipping_address.city,
            shipping_address.state_province or '',
            shipping_address.postal_code or '',
            shipping_address.country,
        ]
        delivery_location = ', '.join([part.strip() for part in address_parts if part.strip()])
    
    return recipient_name, delivery_location


@login_required
def deliveries_list_view(request):
    """List all deliveries with filtering and search."""
    deliveries = Delivery.objects.select_related('invoice', 'invoice__client').all()
    
    # Filtering
    status = request.GET.get('status')
    if status:
        deliveries = deliveries.filter(status=status)
    
    delivery_method = request.GET.get('method')
    if delivery_method:
        deliveries = deliveries.filter(delivery_method=delivery_method)
    
    # Search
    search = request.GET.get('q')
    if search:
        deliveries = deliveries.filter(
            Q(delivery_number__icontains=search) |
            Q(invoice__invoice_number__icontains=search) |
            Q(invoice__client__name__icontains=search) |
            Q(tracking_number__icontains=search)
        )
    
    context = {
        'page_title': 'Deliveries',
        'deliveries': deliveries,
        'statuses': Delivery.STATUS_CHOICES,
        'methods': Delivery._meta.get_field('delivery_method').choices,
        'selected_status': status,
        'selected_method': delivery_method,
        'search_query': search,
    }
    return render(request, '14_deliveries/deliveries_list.html', context)


@login_required
def delivery_detail_view(request, pk):
    """View detailed delivery information."""
    delivery = get_object_or_404(Delivery, pk=pk)
    line_items = delivery.line_items.select_related('product').all()
    
    context = {
        'page_title': f'Delivery {delivery.delivery_number}',
        'delivery': delivery,
        'line_items': line_items,
        'invoice': delivery.invoice,
    }
    return render(request, '14_deliveries/delivery_detail.html', context)


@login_required
def delivery_create_view(request, invoice_id=None):
    """Create a new delivery (optionally for a specific invoice)."""
    # Check for invoice_id from path parameter, query parameter, or form POST
    if not invoice_id:
        # Check query parameters (?invoice=2 or ?invoice_id=2)
        invoice_id = request.GET.get('invoice_id') or request.GET.get('invoice')
    
    # Convert to int if it's a string
    if invoice_id:
        try:
            invoice_id = int(invoice_id)
            invoice = Invoice.objects.select_related('client').get(id=invoice_id, is_active=True)
        except (ValueError, Invoice.DoesNotExist):
            invoice = None
    else:
        invoice = None
    
    if request.method == 'POST':
        invoice_id = request.POST.get('invoice_id')
        try:
            invoice_id = int(invoice_id)
            invoice = get_object_or_404(Invoice, id=invoice_id)
        except (ValueError, TypeError):
            messages.error(request, 'Invalid invoice ID')
            return redirect('deliveries:create')
        
        # Create delivery
        delivery = Delivery.objects.create(
            invoice=invoice,
            scheduled_date=request.POST.get('scheduled_date') or timezone.now().date(),
            actual_delivery_date=request.POST.get('actual_delivery_date') or None,
            delivery_time=request.POST.get('delivery_time') or None,
            delivery_method=request.POST.get('delivery_method', 'hand_delivery'),
            delivery_location=request.POST.get('delivery_location', ''),
            recipient_name=request.POST.get('recipient_name', ''),
            condition=request.POST.get('condition', 'good'),
            condition_notes=request.POST.get('condition_notes', ''),
            notes=request.POST.get('notes', ''),
            created_by=request.user,
            is_active=True,
        )
        
        # Add line items from invoice
        from invoicing_app.invoices.models import InvoiceLineItem
        invoice_lines = InvoiceLineItem.objects.filter(invoice=invoice)
        
        for line in invoice_lines:
            DeliveryLineItem.objects.create(
                delivery=delivery,
                invoice_line=line,
                product=line.product,
                quantity_scheduled=line.quantity,
                quantity_delivered=line.quantity,  # Default to full delivery
                unit=line.product.unit if line.product else 'pcs',
                description=line.description,
            )
        
        # Auto-update status based on delivery completion
        if delivery.is_fully_delivered:
            delivery.status = 'delivered'
            delivery.save(update_fields=['status'])
        
        messages.success(request, f'Delivery {delivery.delivery_number} created successfully!')
        return redirect('deliveries:detail', pk=delivery.id)
    
    # Get invoices for selection (exclude invoices that already have deliveries)
    invoices = Invoice.objects.filter(
        is_active=True,
        status__in=['issued', 'sent', 'viewed', 'paid', 'partial']
    ).select_related('client').exclude(
        deliveries__is_active=True
    ).distinct().order_by('-invoice_date')
    
    # Get auto-populated data if invoice is pre-selected
    auto_recipient_name = ''
    auto_delivery_location = ''
    if invoice:
        auto_recipient_name, auto_delivery_location = get_client_delivery_info(invoice.client)
        # Make sure selected invoice is in the list for the dropdown
        if invoice not in list(invoices):
            # Add it to the list if it exists but doesn't match status filter
            invoices = list(invoices)
            invoices.insert(0, invoice)
    
    context = {
        'page_title': 'Create Delivery',
        'invoices': invoices,
        'selected_invoice': invoice,
        'auto_recipient_name': auto_recipient_name,
        'auto_delivery_location': auto_delivery_location,
        'delivery_methods': Delivery._meta.get_field('delivery_method').choices,
        'conditions': Delivery._meta.get_field('condition').choices,
    }
    return render(request, '14_deliveries/delivery_form.html', context)


@login_required
def delivery_edit_view(request, pk):
    """Edit existing delivery."""
    delivery = get_object_or_404(Delivery, pk=pk)
    
    if request.method == 'POST':
        # Update delivery details
        delivery.scheduled_date = request.POST.get('scheduled_date') or delivery.scheduled_date
        delivery.actual_delivery_date = request.POST.get('actual_delivery_date') or delivery.actual_delivery_date
        delivery.delivery_time = request.POST.get('delivery_time') or delivery.delivery_time
        delivery.delivery_method = request.POST.get('delivery_method', delivery.delivery_method)
        delivery.delivery_location = request.POST.get('delivery_location', delivery.delivery_location)
        delivery.recipient_name = request.POST.get('recipient_name', '')
        delivery.status = request.POST.get('status', delivery.status)
        delivery.condition = request.POST.get('condition', delivery.condition)
        delivery.condition_notes = request.POST.get('condition_notes', '')
        delivery.notes = request.POST.get('notes', '')
        delivery.save()
        
        # Update line items quantities
        for line_item in delivery.line_items.all():
            qty_key = f'qty_delivered_{line_item.id}'
            if qty_key in request.POST:
                line_item.quantity_delivered = request.POST.get(qty_key)
                line_item.save()
        
        # Auto-update status based on deliveries
        if delivery.is_fully_delivered:
            delivery.status = 'delivered'
            delivery.save(update_fields=['status'])
        elif delivery.is_partially_delivered:
            delivery.status = 'partially_delivered'
            delivery.save(update_fields=['status'])
        
        messages.success(request, 'Delivery updated successfully!')
        return redirect('deliveries:detail', pk=delivery.id)
    
    line_items = delivery.line_items.select_related('product').all()
    
    context = {
        'page_title': f'Edit {delivery.delivery_number}',
        'delivery': delivery,
        'line_items': line_items,
        'statuses': Delivery.STATUS_CHOICES,
        'delivery_methods': Delivery._meta.get_field('delivery_method').choices,
        'conditions': Delivery._meta.get_field('condition').choices,
    }
    return render(request, '14_deliveries/delivery_form.html', context)


@login_required
def delivery_pdf_view(request, pk):
    """Generate and display delivery challan PDF."""
    from invoicing_app.notifications.pdf_service import PDFService
    from django.http import HttpResponse
    
    delivery = get_object_or_404(Delivery, pk=pk)
    
    try:
        # Generate PDF (checks for existing first)
        pdf_path = PDFService.generate_delivery_pdf(delivery.id, save=True)
        
        # Return file
        from django.core.files.storage import default_storage
        with default_storage.open(pdf_path, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="delivery_{delivery.delivery_number}.pdf"'
        
        return response
    except Exception as e:
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect('deliveries:detail', pk=pk)


@login_required
@require_http_methods(["POST"])
def delivery_delete_view(request, pk):
    """Delete a delivery (only if draft)."""
    delivery = get_object_or_404(Delivery, pk=pk)
    
    if delivery.status != 'draft':
        messages.error(request, 'Only draft deliveries can be deleted.')
        return redirect('deliveries:detail', pk=pk)
    
    invoice_id = delivery.invoice.id
    delivery_number = delivery.delivery_number
    delivery.delete()
    
    messages.success(request, f'Delivery {delivery_number} deleted successfully!')
    return redirect('invoices:detail', pk=invoice_id)


@login_required
def invoice_details_api(request, invoice_id):
    """Get invoice details for auto-populating delivery form (JSON)."""
    invoice = get_object_or_404(Invoice, id=invoice_id, is_active=True)
    
    # Get auto-populated data from helper function
    recipient_name, delivery_location = get_client_delivery_info(invoice.client)
    
    return JsonResponse({
        'invoice_number': invoice.invoice_number,
        'client_name': invoice.client.name,
        'client_email': invoice.client.email or '',
        'client_phone': invoice.client.phone or '',
        'recipient_name': recipient_name,
        'delivery_location': delivery_location,
        'total_amount': str(invoice.total_amount),
        'currency': invoice.currency,
    })
