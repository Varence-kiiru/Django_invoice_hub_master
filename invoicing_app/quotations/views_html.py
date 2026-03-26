"""
HTML Views for Quote management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import datetime
import json
import logging
from decimal import Decimal
from .models import Quote, QuoteLineItem
from .forms import QuoteForm, QuoteLineItemFormSet
from .services import QuoteNumberService, QuoteConversionService, QuoteStatusService
from invoicing_app.clients.models import Client
from invoicing_app.products.models import Product, ProductTaxClass
from invoicing_app.taxes.models import TaxRate, VATRule
from invoicing_app.notifications.pdf_service import PDFService
from invoicing_app.core.models import CompanySettings, SavedFilter
from invoicing_app.core.search_filters import AdvancedFilterBuilder, FullTextSearch, parse_url_filters

logger = logging.getLogger(__name__)


@login_required
def quotes_list_view(request):
    """List all quotes with advanced filtering and full-text search."""
    quotes = Quote.objects.select_related('client').order_by('-quote_date')

    # Parse URL filters using advanced filter builder
    criteria = parse_url_filters(request.GET)
    if criteria:
        quotes = AdvancedFilterBuilder.apply_quotation_filters(quotes, criteria)

    # Full-text search
    search_query = request.GET.get('q', '')
    if search_query:
        quotes = FullTextSearch.search_quotations(quotes, search_query)

    # Get user's saved filters
    user_filters = SavedFilter.get_user_filters(request.user, 'quotation')

    # Count active filters for badge
    total_filters = len([v for v in criteria.values() if v])

    # Prepare context with all filter parameters
    context = {
        'quotes': quotes,
        'user_filters': user_filters,
        'current_filters': criteria,
        'total_filters': total_filters,
        'status': request.GET.get('status', ''),
        'client_name': request.GET.get('client_name', ''),
        'quote_number': request.GET.get('quote_number', ''),
        'min_amount': request.GET.get('min_amount', ''),
        'max_amount': request.GET.get('max_amount', ''),
        'from_date': request.GET.get('from_date', ''),
        'to_date': request.GET.get('to_date', ''),
        'valid_until_from': request.GET.get('valid_until_from', ''),
        'valid_until_to': request.GET.get('valid_until_to', ''),
        'is_expired': request.GET.get('is_expired', ''),
        'search_query': search_query,
        'statuses': Quote.STATUS_CHOICES,
    }
    return render(request, '13_quotations/quotes_list.html', context)


@login_required
def quote_create_view(request):
    """Create new quote (draft)."""
    if request.method == 'POST':
        try:
            from datetime import timedelta
            
            # Get the quote prefix from company settings
            try:
                settings = CompanySettings.objects.get()
                prefix = settings.quote_prefix
            except CompanySettings.DoesNotExist:
                prefix = 'QUOTE'  # Fallback to default
            
            # Generate quote number using the service
            quote_number = QuoteNumberService.generate_next_number(prefix=prefix)
            
            today = timezone.now().date()
            quote = Quote.objects.create(
                quote_number=quote_number,
                client_id=request.POST.get('client'),
                quote_date=today,
                valid_until=request.POST.get('valid_until') or (today + timedelta(days=30)),
                description=request.POST.get('description', '').strip(),
                currency=request.POST.get('currency', 'KES'),
                status='draft',
                created_by=request.user,
                updated_by=request.user,
            )
            
            messages.success(request, f'Quote {quote_number} created successfully!')
            return redirect('quotations:detail', pk=quote.id)
        except Exception as e:
            messages.error(request, f'Error creating quote: {str(e)}')
    
    context = {
        'page_title': 'Create Quote',
        'clients': Client.objects.filter(is_active=True),
    }
    return render(request, '13_quotations/quote_form.html', context)


@login_required
def add_quote_line_item_view(request, pk):
    """Add line item to quote."""
    quote = get_object_or_404(Quote, pk=pk)
    
    if quote.status != 'draft':
        messages.error(request, 'Can only add line items to draft quotes')
        return redirect('quotations:detail', pk=pk)
    
    if request.method == 'POST':
        try:
            product_id = request.POST.get('product')
            quantity = Decimal(request.POST.get('quantity', 1))
            unit_price = Decimal(request.POST.get('unit_price'))
            tax_rate_id = request.POST.get('tax_rate')
            
            # Calculate line amount
            line_amount = quantity * unit_price
            
            # Get tax rate and calculate tax amount
            tax_rate = TaxRate.objects.get(id=tax_rate_id) if tax_rate_id else None
            tax_amount = line_amount * (tax_rate.rate_percentage / 100) if tax_rate else Decimal(0)
            line_total = line_amount + tax_amount
            
            line_item = QuoteLineItem.objects.create(
                quote=quote,
                product_id=product_id if product_id else None,
                description=request.POST.get('description', ''),
                quantity=quantity,
                unit_price=unit_price,
                line_amount=line_amount,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                line_total=line_total,
            )
            
            messages.success(request, 'Line item added successfully')
            return redirect('quotations:detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Error adding line item: {str(e)}')
    
    # Get active tax rates for dropdown
    from django.utils import timezone
    today = timezone.now().date()
    active_tax_rates = TaxRate.objects.filter(
        effective_from__lte=today
    ).filter(
        Q(effective_to__isnull=True) | Q(effective_to__gte=today)
    ).order_by('tax_type', 'rate_percentage')
    
    # Build tax class to rate mapping for JavaScript
    # Map ProductTaxClass.rate_type to the appropriate TaxRate via VATRule
    tax_class_rate_map = {}
    
    print(f'\n{"="*70}')
    print(f'[add_quote_line_item_view] Building tax class rate map')
    print(f'{"="*70}')
    
    # Note: ProductTaxClass doesn't have is_active field, so just get all
    for tax_class in ProductTaxClass.objects.all():
        # Get the VATRule for this tax class with the highest priority
        vat_rule = VATRule.objects.filter(
            tax_class=tax_class,
            is_active=True
        ).order_by('-priority').first()
        
        print(f'Processing: {tax_class.name} (rate_type: {tax_class.rate_type})')
        
        if vat_rule:
            print(f'  Found VATRule ID: {vat_rule.id}')
            if vat_rule.tax_rate:
                print(f'  Found TaxRate: {vat_rule.tax_rate.name} ({vat_rule.tax_rate.rate_percentage}%)')
                tax_class_rate_map[tax_class.rate_type] = {
                    'rate_id': vat_rule.tax_rate.id,
                    'percentage': float(vat_rule.tax_rate.rate_percentage),
                    'name': vat_rule.tax_rate.name
                }
                print(f'  Added to map!')
            else:
                print(f'  ERROR: VATRule has NO tax_rate!')
        else:
            print(f'  ERROR: NO VATRule found!')
    
    print(f'Final map: {tax_class_rate_map}')
    print(f'JSON output: {json.dumps(tax_class_rate_map)}')
    print(f'{"="*70}\n')
    
    return render(request, '13_quotations/add_line_item.html', {
        'quote': quote,
        'products': Product.objects.filter(is_active=True),
        'tax_rates': active_tax_rates,
        'tax_class_rate_map': json.dumps(tax_class_rate_map),
    })


@login_required
def edit_quote_line_item_view(request, pk, item_id):
    """Edit line item in quote."""
    quote = get_object_or_404(Quote, pk=pk)
    line_item = get_object_or_404(QuoteLineItem, pk=item_id, quote=quote)
    
    if quote.status != 'draft':
        messages.error(request, 'Can only edit line items in draft quotes')
        return redirect('quotations:detail', pk=pk)
    
    if request.method == 'POST':
        try:
            product_id = request.POST.get('product')
            line_item.product_id = product_id if product_id else None
            line_item.description = request.POST.get('description', '')
            line_item.quantity = Decimal(request.POST.get('quantity', 1))
            line_item.unit_price = Decimal(request.POST.get('unit_price'))
            
            # Calculate line amount
            line_item.line_amount = line_item.quantity * line_item.unit_price
            
            # Get tax rate and calculate tax amount
            tax_rate_id = request.POST.get('tax_rate')
            line_item.tax_rate = TaxRate.objects.get(id=tax_rate_id) if tax_rate_id else None
            line_item.tax_amount = line_item.line_amount * (line_item.tax_rate.rate_percentage / 100) if line_item.tax_rate else Decimal(0)
            line_item.line_total = line_item.line_amount + line_item.tax_amount
            
            line_item.save()
            
            messages.success(request, 'Line item updated successfully')
            return redirect('quotations:detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Error updating line item: {str(e)}')
    
    # Get active tax rates for dropdown
    from django.utils import timezone
    today = timezone.now().date()
    active_tax_rates = TaxRate.objects.filter(
        effective_from__lte=today
    ).filter(
        Q(effective_to__isnull=True) | Q(effective_to__gte=today)
    ).order_by('tax_type', 'rate_percentage')
    
    # Build tax class to rate mapping for JavaScript
    # Map ProductTaxClass.rate_type to the appropriate TaxRate via VATRule
    tax_class_rate_map = {}
    
    print(f'\n{"="*70}')
    print(f'[edit_quote_line_item_view] Building tax class rate map')
    print(f'{"="*70}')
    
    for tax_class in ProductTaxClass.objects.filter(is_active=True):
        # Get the VATRule for this tax class with the highest priority
        vat_rule = VATRule.objects.filter(
            tax_class=tax_class,
            is_active=True
        ).order_by('-priority').first()
        
        print(f'Processing: {tax_class.name} (rate_type: {tax_class.rate_type})')
        
        if vat_rule:
            print(f'  Found VATRule ID: {vat_rule.id}')
            if vat_rule.tax_rate:
                print(f'  Found TaxRate: {vat_rule.tax_rate.name} ({vat_rule.tax_rate.rate_percentage}%)')
                tax_class_rate_map[tax_class.rate_type] = {
                    'rate_id': vat_rule.tax_rate.id,
                    'percentage': float(vat_rule.tax_rate.rate_percentage),
                    'name': vat_rule.tax_rate.name
                }
                print(f'  Added to map!')
            else:
                print(f'  ERROR: VATRule has NO tax_rate!')
        else:
            print(f'  ERROR: NO VATRule found!')
    
    print(f'Final map: {tax_class_rate_map}')
    print(f'JSON output: {json.dumps(tax_class_rate_map)}')
    print(f'{"="*70}\n')
    
    return render(request, '13_quotations/edit_line_item.html', {
        'quote': quote,
        'line_item': line_item,
        'products': Product.objects.filter(is_active=True),
        'tax_rates': active_tax_rates,
        'tax_class_rate_map': json.dumps(tax_class_rate_map),
        'current_tax_rate_percentage': line_item.tax_rate.rate_percentage if line_item.tax_rate else 0,
        'current_tax_rate_id': line_item.tax_rate.id if line_item.tax_rate else '',
    })


@login_required
def delete_quote_line_item_view(request, pk, item_id):
    """Delete line item from quote."""
    quote = get_object_or_404(Quote, pk=pk)
    line_item = get_object_or_404(QuoteLineItem, pk=item_id, quote=quote)
    
    if quote.status != 'draft':
        messages.error(request, 'Can only delete line items from draft quotes')
        return redirect('quotations:detail', pk=pk)
    
    if request.method == 'POST':
        try:
            line_item.delete()
            messages.success(request, 'Line item deleted successfully')
        except Exception as e:
            messages.error(request, f'Error deleting line item: {str(e)}')
    
    return redirect('quotations:detail', pk=pk)


@login_required
def quote_detail_view(request, pk):
    """Show quote details."""
    quote = get_object_or_404(Quote, pk=pk)
    settings = CompanySettings.get_settings()
    return render(request, '13_quotations/quote_detail.html', {
        'quote': quote,
        'settings': settings,
    })


@login_required
def quote_edit_view(request, pk):
    """Edit existing quote details (client, dates, memo)."""
    quote = get_object_or_404(Quote, pk=pk)

    # Only allow editing drafts
    if quote.status != 'draft':
        messages.error(request, 'Only draft quotes can be edited')
        return redirect('quotations:detail', pk=pk)

    if request.method == 'POST':
        try:
            quote.client_id = request.POST.get('client')
            quote.quote_date = request.POST.get('quote_date') or quote.quote_date
            quote.valid_until = request.POST.get('valid_until') or quote.valid_until
            quote.description = request.POST.get('description', '').strip()
            quote.currency = request.POST.get('currency', 'KES')
            quote.updated_by = request.user
            quote.save()

            messages.success(request, f'Quote {quote.quote_number} updated')
            return redirect('quotations:detail', pk=quote.pk)
        except Exception as e:
            messages.error(request, f'Error updating quote: {str(e)}')

    context = {
        'page_title': 'Edit Quote',
        'clients': Client.objects.filter(is_active=True),
        'quote': quote,
    }
    return render(request, '13_quotations/quote_edit.html', context)


@login_required
def quote_delete_view(request, pk):
    """Delete a quote."""
    quote = get_object_or_404(Quote, pk=pk)

    if request.method == 'POST':
        quote_number = quote.quote_number
        quote.is_active = False
        quote.save()
        messages.success(request, f'Quote {quote_number} deleted')
        return redirect('quotations:list')

    return render(request, '13_quotations/quote_delete_confirm.html', {
        'quote': quote,
    })


@login_required
def quote_convert_view(request, pk):
    """Convert accepted quote to invoice."""
    from .email_service import QuoteEmailService
    from datetime import timedelta
    quote = get_object_or_404(Quote, pk=pk)

    if quote.status != 'accepted':
        messages.error(
            request,
            'Only accepted quotes can be converted to invoices'
        )
        return redirect('quotations:detail', pk=pk)

    if request.method == 'POST':
        from datetime import datetime
        invoice_date_str = request.POST.get('invoice_date')
        due_date_str = request.POST.get('due_date')

        try:
            invoice_date = datetime.strptime(invoice_date_str, '%Y-%m-%d').date() if invoice_date_str else None
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()

            invoice = QuoteConversionService.convert_quote_to_invoice(
                quote,
                invoice_date=invoice_date,
                due_date=due_date
            )
            
            # Send conversion notification email
            try:
                email_service = QuoteEmailService()
                email_service.send_quote_converted(
                    client_email=quote.client.email,
                    client_name=quote.client.name,
                    quote_number=quote.quote_number,
                    invoice_number=invoice.invoice_number,
                    total_amount=f"{quote.currency} {quote.total_amount:,.2f}",
                    due_date=due_date.strftime('%B %d, %Y')
                )
            except Exception as e:
                logger.error(f"Failed to send quote_converted email: {str(e)}")
            
            messages.success(
                request,
                f'Quote converted to invoice {invoice.invoice_number}'
            )
            return redirect('invoices:detail', pk=invoice.pk)
        except ValueError as e:
            messages.error(request, str(e))

    # Pre-fill default dates based on client's payment terms
    today = timezone.now().date()
    default_due_date = today + timedelta(days=quote.client.payment_terms_days)
    
    return render(request, '13_quotations/quote_convert.html', {
        'quote': quote,
        'today': today,
        'default_due_date': default_due_date,
        'payment_terms_days': quote.client.payment_terms_days,
    })


@login_required
def quote_send_view(request, pk):
    """Send quotation to client via email with PDF attachment."""
    from django.contrib import messages
    from django.http import JsonResponse
    from invoicing_app.notifications.email_service import email_service
    from invoicing_app.notifications.pdf_service import pdf_service
    
    quote = get_object_or_404(Quote, pk=pk)
    
    if request.method == 'POST':
        try:
            # Generate PDF for quote
            pdf_content = pdf_service.generate_quote_pdf(quote.id, save=False)
            
            # Send email with PDF attachment
            success = email_service.send_quote_issued_notification(
                client_email=quote.client.email,
                client_name=quote.client.name,
                quote_number=quote.quote_number,
                quote_date=quote.quote_date.strftime('%B %d, %Y'),
                total_amount=f"{quote.currency} {quote.total_amount:,.2f}",
                valid_until=quote.valid_until.strftime('%B %d, %Y'),
                pdf_content=pdf_content.getvalue() if hasattr(pdf_content, 'getvalue') else pdf_content,
            )
            
            if success:
                # Update quote status
                quote.status = 'sent'
                quote.sent_at = timezone.now()
                quote.updated_by = request.user
                quote.save()
                
                # Return JSON response
                return JsonResponse({
                    'success': True,
                    'message': f'Quotation {quote.quote_number} sent successfully to {quote.client.email}!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'Failed to send quotation {quote.quote_number}. Please try again.'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error sending quotation: {str(e)}'
            })
    
    context = {'quote': quote}
    return render(request, '13_quotations/quote_send_email.html', context)


@login_required
def quote_pdf_view(request, pk):
    """Generate and display PDF preview for quotation."""
    import qrcode
    from io import BytesIO
    import base64
    
    quote = get_object_or_404(Quote, pk=pk)
    
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
        
        # Generate QR code that links to the quotation
        qr_url = request.build_absolute_uri(f'/quotations/{quote.id}/')
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        # Convert QR code to image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 data URI
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        qr_data = base64.b64encode(qr_buffer.getvalue()).decode()
        qr_data_uri = f'data:image/png;base64,{qr_data}'
        
        # Prepare context with company information
        context = {
            'quote': quote,
            'company_settings': company_settings,
            'company_logo': company_logo,
            'quote_qr_code': qr_data_uri,
        }
        
        logger.info(f"Rendered PDF preview for quotation {quote.quote_number}")
        return render(request, '13_quotations/quote_pdf.html', context)
    except Exception as e:
        logger.error(f"Error rendering PDF preview for quotation {pk}: {str(e)}")
        messages.error(request, f"Error generating PDF preview: {str(e)}")
        return redirect('quotations:detail', pk=pk)


@login_required
def quote_print_view(request, pk):
    """Open quotation PDF in new tab for printing."""
    from django.http import HttpResponse
    from invoicing_app.notifications.pdf_service import PDFService
    from django.core.files.storage import default_storage
    from django.contrib import messages
    
    quote = get_object_or_404(Quote, pk=pk)
    
    try:
        # Generate/retrieve PDF (checks for existing cached PDF first)
        pdf_path = PDFService.generate_quote_pdf(quote.id, save=True)
        
        # Open and return the file inline for printing
        with default_storage.open(pdf_path, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="quotation_{quote.quote_number}.pdf"'
        
        logger.info(f"Opened quotation PDF {quote.quote_number} for printing")
        return response
    except Exception as e:
        logger.error(f"Error generating PDF for quotation {pk}: {str(e)}")
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect('quotations:detail', pk=pk)


@login_required
def quote_issue_confirm_view(request, pk):
    """Confirm and issue quotation."""
    from django.contrib import messages
    quote = get_object_or_404(Quote, pk=pk, status='draft', is_active=True)
    if request.method == 'POST':
        quote.status = 'issued'
        quote.issued_at = timezone.now()
        quote.save()
        messages.success(request, f'Quotation {quote.quote_number} issued!')
        return redirect('quotations:detail', pk=pk)
    context = {'quote': quote}
    return render(request, '13_quotations/quote_issue_confirm.html', context)


@login_required
def quote_accept_view(request, pk):
    """Manually mark quotation as accepted (for oral approval)."""
    from django.contrib import messages
    from .email_service import QuoteEmailService
    
    quote = get_object_or_404(Quote, pk=pk, is_active=True)
    
    # Only issued, sent, or viewed quotes can be manually accepted
    if quote.status not in ['issued', 'sent', 'viewed']:
        messages.error(request, f'Quotation with status "{quote.get_status_display()}" cannot be accepted.')
        return redirect('quotations:detail', pk=pk)
    
    if request.method == 'POST':
        try:
            quote.status = 'accepted'
            quote.accepted_at = timezone.now()
            quote.save()
            
            # Send acceptance notification email to client
            try:
                email_service = QuoteEmailService()
                email_service.send_quote_accepted(
                    client_email=quote.client.email,
                    client_name=quote.client.name,
                    quote_number=quote.quote_number,
                    total_amount=f"{quote.currency} {quote.total_amount:,.2f}",
                    valid_until=quote.valid_until.strftime('%B %d, %Y')
                )
            except Exception as e:
                logger.error(f"Failed to send quote_accepted email: {str(e)}")
            
            messages.success(request, f'Quotation {quote.quote_number} marked as accepted!')
            return redirect('quotations:detail', pk=pk)
        except Exception as e:
            logger.error(f"Error accepting quotation {pk}: {str(e)}")
            messages.error(request, f'Error accepting quotation: {str(e)}')
            return redirect('quotations:detail', pk=pk)
    
    # GET request - show confirmation page
    context = {'quote': quote}
    return render(request, '13_quotations/quote_accept_confirm.html', context)


@login_required
def quote_download_view(request, pk):
    """Download quotation PDF as attachment."""
    from django.http import HttpResponse
    from invoicing_app.notifications.pdf_service import PDFService
    from django.core.files.storage import default_storage
    
    quote = get_object_or_404(Quote, pk=pk)
    
    try:
        # Generate/retrieve PDF (checks for existing cached PDF first)
        pdf_path = PDFService.generate_quote_pdf(quote.id, save=True)
        
        # Open and return the file for download
        with default_storage.open(pdf_path, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="quotation_{quote.quote_number}.pdf"'
        
        logger.info(f"Downloaded quotation PDF {quote.quote_number}")
        return response
    except Exception as e:
        logger.error(f"Error downloading PDF for quotation {pk}: {str(e)}")
        messages.error(request, f"Error downloading PDF: {str(e)}")
        return redirect('quotations:detail', pk=pk)
