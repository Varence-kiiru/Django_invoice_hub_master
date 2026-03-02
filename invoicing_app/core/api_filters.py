"""
API views for Advanced Search & Filtering system
Handles filter CRUD operations and search suggestions
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import json

from invoicing_app.core.models import SavedFilter
from invoicing_app.invoices.models import Invoice
from invoicing_app.payments.models import Payment
from invoicing_app.clients.models import Client
from invoicing_app.quotations.models import Quote
from invoicing_app.core.search_filters import get_filter_options


@login_required
@require_http_methods(["GET", "POST"])
def filter_api(request):
    """Get or create saved filters"""
    if request.method == 'GET':
        # Get user's saved filters
        filters = SavedFilter.get_user_filters(request.user)
        
        filters_data = [{
            'id': f.id,
            'name': f.name,
            'description': f.description,
            'filter_type': f.filter_type,
            'filter_criteria': f.filter_criteria,
            'is_global': f.is_global,
            'created_by': f.created_by.get_full_name() or f.created_by.username,
            'last_used': f.last_used.isoformat() if f.last_used else None,
            'use_count': f.use_count,
        } for f in filters]
        
        return JsonResponse({'filters': filters_data})
    
    else:  # POST - Create new filter
        try:
            data = json.loads(request.body)
            
            filter_obj = SavedFilter.objects.create(
                name=data.get('name'),
                description=data.get('description', ''),
                filter_type=data.get('filter_type'),
                filter_criteria=data.get('filter_criteria', {}),
                created_by=request.user,
                is_global=data.get('is_global', False)
            )
            
            return JsonResponse({
                'success': True,
                'id': filter_obj.id,
                'message': 'Filter saved successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


@login_required
@require_http_methods(["GET", "PATCH", "DELETE"])
def filter_detail_api(request, filter_id):
    """Get, update, or delete a specific saved filter"""
    try:
        filter_obj = SavedFilter.objects.get(id=filter_id)
        
        # Check permission (owner or global filter)
        if filter_obj.created_by != request.user and not filter_obj.is_global:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        if request.method == 'GET':
            # Record usage
            filter_obj.record_usage()
            
            return JsonResponse({
                'id': filter_obj.id,
                'name': filter_obj.name,
                'description': filter_obj.description,
                'filter_type': filter_obj.filter_type,
                'filter_criteria': filter_obj.filter_criteria,
                'is_global': filter_obj.is_global,
                'created_by': filter_obj.created_by.get_full_name() or filter_obj.created_by.username,
                'last_used': filter_obj.last_used.isoformat() if filter_obj.last_used else None,
                'use_count': filter_obj.use_count,
            })
        
        elif request.method == 'PATCH':
            # Update filter
            if filter_obj.created_by != request.user:
                return JsonResponse({'error': 'Only filter owner can edit'}, status=403)
            
            data = json.loads(request.body)
            filter_obj.name = data.get('name', filter_obj.name)
            filter_obj.description = data.get('description', filter_obj.description)
            filter_obj.filter_criteria = data.get('filter_criteria', filter_obj.filter_criteria)
            filter_obj.is_global = data.get('is_global', filter_obj.is_global)
            filter_obj.save()
            
            return JsonResponse({'success': True, 'message': 'Filter updated'})
        
        elif request.method == 'DELETE':
            # Delete filter
            if filter_obj.created_by != request.user:
                return JsonResponse({'error': 'Only filter owner can delete'}, status=403)
            
            filter_obj.delete()
            return JsonResponse({'success': True, 'message': 'Filter deleted'})
    
    except SavedFilter.DoesNotExist:
        return JsonResponse({'error': 'Filter not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_http_methods(["GET"])
def filter_options_api(request):
    """Get available filter options for each type"""
    filter_type = request.GET.get('type', 'invoice')
    options = get_filter_options(filter_type)
    return JsonResponse({'options': options})


@login_required
@require_http_methods(["GET"])
def search_suggestions_api(request):
    """Get search suggestions for global search"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': {}})
    
    suggestions = {
        'invoices': [],
        'payments': [],
        'clients': [],
        'quotations': [],
    }
    
    # Search invoices
    invoice_results = Invoice.objects.filter(
        Q(invoice_number__icontains=query) |
        Q(client__name__icontains=query),
        is_active=True
    ).select_related('client').values('id', 'invoice_number', 'client__name')[:5]
    
    suggestions['invoices'] = [
        {
            'id': inv['id'],
            'invoice_number': inv['invoice_number'],
            'client_name': inv['client__name']
        }
        for inv in invoice_results
    ]
    
    # Search payments
    payment_results = Payment.objects.filter(
        Q(invoice__invoice_number__icontains=query) |
        Q(invoice__client__name__icontains=query) |
        Q(transaction_reference__icontains=query)
    ).select_related('invoice', 'invoice__client').values(
        'id', 'invoice__invoice_number', 'invoice__client__name'
    )[:5]
    
    suggestions['payments'] = [
        {
            'id': pay['id'],
            'invoice_number': pay['invoice__invoice_number'],
            'client_name': pay['invoice__client__name']
        }
        for pay in payment_results
    ]
    
    # Search clients
    client_results = Client.objects.filter(
        Q(name__icontains=query) |
        Q(email__icontains=query) |
        Q(tax_id__icontains=query)
    ).values('id', 'name', 'email')[:5]
    
    suggestions['clients'] = [
        {
            'id': c['id'],
            'name': c['name'],
            'email': c['email']
        }
        for c in client_results
    ]
    
    # Search quotations
    quote_results = Quote.objects.filter(
        Q(quote_number__icontains=query) |
        Q(client__name__icontains=query),
        is_active=True
    ).select_related('client').values('id', 'quote_number', 'client__name')[:5]
    
    suggestions['quotations'] = [
        {
            'id': q['id'],
            'quote_number': q['quote_number'],
            'client_name': q['client__name']
        }
        for q in quote_results
    ]
    
    return JsonResponse({'suggestions': suggestions})
