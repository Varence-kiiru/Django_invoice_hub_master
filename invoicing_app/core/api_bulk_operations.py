"""
API endpoints for bulk operations on invoices, payments, clients, and quotations.
Handles batch actions like status updates, email sending, and deletion.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
import json
import logging

from invoicing_app.invoices.models import Invoice
from invoicing_app.payments.models import Payment
from invoicing_app.clients.models import Client
from invoicing_app.quotations.models import Quote
from invoicing_app.notifications.email_service import EmailService

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def bulk_status_update(request):
    """Update status for multiple items"""
    try:
        data = json.loads(request.body)
        
        entity_type = data.get('entity_type', '').rstrip('s')  # Normalize: invoices -> invoice
        item_ids = data.get('ids', [])  # List of IDs
        new_status = data.get('status')
        
        if not entity_type or not item_ids or not new_status:
            return JsonResponse({
                'success': False,
                'error': 'Missing required parameters'
            }, status=400)
        
        updated_count = 0
        errors = []
        
        if entity_type == 'invoice':
            for invoice_id in item_ids:
                try:
                    invoice = Invoice.objects.get(id=invoice_id)
                    # Check permission - user must own the invoice (via company)
                    invoice.status = new_status
                    invoice.save()
                    updated_count += 1
                except Invoice.DoesNotExist:
                    errors.append(f'Invoice {invoice_id} not found')
                except Exception as e:
                    errors.append(f'Invoice {invoice_id}: {str(e)}')
        
        elif entity_type == 'payment':
            for payment_id in item_ids:
                try:
                    payment = Payment.objects.get(id=payment_id)
                    payment.status = new_status
                    payment.save()
                    updated_count += 1
                except Payment.DoesNotExist:
                    errors.append(f'Payment {payment_id} not found')
                except Exception as e:
                    errors.append(f'Payment {payment_id}: {str(e)}')
        
        elif entity_type == 'quotation':
            for quote_id in item_ids:
                try:
                    quote = Quote.objects.get(id=quote_id)
                    quote.status = new_status
                    quote.save()
                    updated_count += 1
                except Quote.DoesNotExist:
                    errors.append(f'Quote {quote_id} not found')
                except Exception as e:
                    errors.append(f'Quote {quote_id}: {str(e)}')
        
        elif entity_type == 'client':
            for client_id in item_ids:
                try:
                    client = Client.objects.get(id=client_id)
                    # For clients, handle is_active status
                    if new_status in ['active', 'inactive']:
                        client.is_active = (new_status == 'active')
                        client.save()
                        updated_count += 1
                    else:
                        errors.append(f'Client {client_id}: Invalid status for client')
                except Client.DoesNotExist:
                    errors.append(f'Client {client_id} not found')
                except Exception as e:
                    errors.append(f'Client {client_id}: {str(e)}')
        
        else:
            return JsonResponse({
                'success': False,
                'error': f'Unknown entity type: {entity_type}'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'updated_count': updated_count,
            'errors': errors,
            'message': f'Successfully updated {updated_count} items'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f'Bulk status update error: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def bulk_send_email(request):
    """Send emails to multiple recipients"""
    try:
        data = json.loads(request.body)
        
        entity_type = data.get('entity_type', '').rstrip('s')  # Normalize: invoices -> invoice
        item_ids = data.get('ids', [])
        email_type = data.get('email_type')  # invoice, reminder, custom
        custom_subject = data.get('subject')
        custom_message = data.get('message')
        
        if not entity_type or not item_ids:
            return JsonResponse({
                'success': False,
                'error': 'Missing required parameters'
            }, status=400)
        
        sent_count = 0
        errors = []
        
        if entity_type == 'invoice':
            for invoice_id in item_ids:
                try:
                    invoice = Invoice.objects.get(id=invoice_id)
                    
                    # Send email based on type
                    if email_type == 'invoice':
                        # Send invoice document
                        EmailService.send_invoice_email(invoice, invoice.client.email)
                    elif email_type == 'reminder':
                        # Send payment reminder
                        EmailService.send_payment_reminder(invoice)
                    elif email_type == 'custom' and custom_subject and custom_message:
                        # Send custom email
                        EmailService.send_custom_email(
                            invoice.client.email,
                            custom_subject,
                            custom_message
                        )
                    
                    sent_count += 1
                except Invoice.DoesNotExist:
                    errors.append(f'Invoice {invoice_id} not found')
                except Exception as e:
                    errors.append(f'Invoice {invoice_id}: {str(e)}')
        
        elif entity_type == 'quotation':
            for quote_id in item_ids:
                try:
                    quote = Quote.objects.get(id=quote_id)
                    
                    if email_type == 'quotation':
                        # Send quotation
                        EmailService.send_quotation_email(quote, quote.client.email)
                    elif email_type == 'reminder':
                        # Send quotation reminder
                        EmailService.send_quotation_reminder(quote)
                    elif email_type == 'custom' and custom_subject and custom_message:
                        EmailService.send_custom_email(
                            quote.client.email,
                            custom_subject,
                            custom_message
                        )
                    
                    sent_count += 1
                except Quote.DoesNotExist:
                    errors.append(f'Quote {quote_id} not found')
                except Exception as e:
                    errors.append(f'Quote {quote_id}: {str(e)}')
        
        elif entity_type == 'client':
            for client_id in item_ids:
                try:
                    client = Client.objects.get(id=client_id)
                    
                    if email_type == 'custom' and custom_subject and custom_message:
                        EmailService.send_custom_email(
                            client.email,
                            custom_subject,
                            custom_message
                        )
                        sent_count += 1
                    else:
                        errors.append(f'Client {client_id}: Unsupported email type for clients')
                except Client.DoesNotExist:
                    errors.append(f'Client {client_id} not found')
                except Exception as e:
                    errors.append(f'Client {client_id}: {str(e)}')
        
        else:
            return JsonResponse({
                'success': False,
                'error': f'Unknown entity type: {entity_type}'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'sent_count': sent_count,
            'errors': errors,
            'message': f'Successfully sent {sent_count} emails'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f'Bulk email error: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def bulk_delete(request):
    """Delete multiple items"""
    try:
        data = json.loads(request.body)
        
        entity_type = data.get('entity_type', '').rstrip('s')  # Normalize: invoices -> invoice
        item_ids = data.get('ids', [])
        
        if not entity_type or not item_ids:
            return JsonResponse({
                'success': False,
                'error': 'Missing required parameters'
            }, status=400)
        
        deleted_count = 0
        errors = []
        
        if entity_type == 'invoice':
            for invoice_id in item_ids:
                try:
                    invoice = Invoice.objects.get(id=invoice_id)
                    invoice.delete()
                    deleted_count += 1
                except Invoice.DoesNotExist:
                    errors.append(f'Invoice {invoice_id} not found')
                except Exception as e:
                    errors.append(f'Invoice {invoice_id}: {str(e)}')
        
        elif entity_type == 'payment':
            for payment_id in item_ids:
                try:
                    payment = Payment.objects.get(id=payment_id)
                    payment.delete()
                    deleted_count += 1
                except Payment.DoesNotExist:
                    errors.append(f'Payment {payment_id} not found')
                except Exception as e:
                    errors.append(f'Payment {payment_id}: {str(e)}')
        
        elif entity_type == 'quotation':
            for quote_id in item_ids:
                try:
                    quote = Quote.objects.get(id=quote_id)
                    quote.delete()
                    deleted_count += 1
                except Quote.DoesNotExist:
                    errors.append(f'Quote {quote_id} not found')
                except Exception as e:
                    errors.append(f'Quote {quote_id}: {str(e)}')
        
        elif entity_type == 'client':
            for client_id in item_ids:
                try:
                    client = Client.objects.get(id=client_id)
                    client.delete()
                    deleted_count += 1
                except Client.DoesNotExist:
                    errors.append(f'Client {client_id} not found')
                except Exception as e:
                    errors.append(f'Client {client_id}: {str(e)}')
        
        else:
            return JsonResponse({
                'success': False,
                'error': f'Unknown entity type: {entity_type}'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'deleted_count': deleted_count,
            'errors': errors,
            'message': f'Successfully deleted {deleted_count} items'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f'Bulk delete error: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def get_bulk_action_options(request):
    """Get available bulk actions for an entity type"""
    try:
        data = json.loads(request.body)
        entity_type = data.get('entity_type', '').rstrip('s')  # Remove trailing 's' for plurals
        
        options = {
            'invoice': {
                'status_options': ['draft', 'sent', 'issued', 'paid', 'partially_paid', 'overdue', 'cancelled'],
                'email_types': ['invoice', 'reminder', 'custom'],
                'can_delete': True,
            },
            'payment': {
                'status_options': ['pending', 'successful', 'failed', 'refunded'],
                'email_types': [],
                'can_delete': True,
            },
            'quotation': {
                'status_options': ['draft', 'issued', 'sent', 'viewed', 'accepted', 'rejected', 'expired', 'converted', 'archived'],
                'email_types': ['quotation', 'reminder', 'custom'],
                'can_delete': True,
            },
            'client': {
                'status_options': ['active', 'inactive'],
                'email_types': ['custom'],
                'can_delete': True,
            },
        }
        
        if entity_type not in options:
            return JsonResponse({
                'success': False,
                'error': f'Unknown entity type: {entity_type}'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'options': options[entity_type]
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f'Get bulk action options error: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
