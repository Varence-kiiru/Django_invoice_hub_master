from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from invoicing_app.invoices.models import Invoice, InvoiceLineItem
from invoicing_app.products.models import Product
from invoicing_app.taxes.models import TaxRate
from invoicing_app.payments.models import Payment
from .serializers import InvoiceSerializer, InvoiceLineItemSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all().order_by('-invoice_date')
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['invoice_number', 'client', 'status', 'invoice_date']
    search_fields = ['invoice_number', 'description']
    
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """Get invoice details including payment breakdown."""
        invoice = self.get_object()
        
        return Response({
            'success': True,
            'invoice_number': invoice.invoice_number,
            'total_amount': float(invoice.total_amount),
            'amount_paid': float(invoice.amount_paid),
            'amount_due': float(invoice.amount_due),
            'currency': invoice.currency,
            'status': invoice.status,
            'client_name': invoice.client.name,
            'invoice_date': invoice.invoice_date.isoformat(),
            'due_date': invoice.due_date.isoformat(),
        })
    
    @action(detail=True, methods=['get'])
    def payment_history(self, request, pk=None):
        """Get payment history for an invoice."""
        invoice = self.get_object()
        
        # Get all payments for this invoice
        payments = Payment.objects.filter(invoice=invoice).order_by('-date_paid')
        
        payment_list = [
            {
                'date': payment.date_paid.strftime('%Y-%m-%d'),
                'amount': float(payment.amount),
                'method': payment.payment_method.name if payment.payment_method else 'Unknown',
                'reference': payment.transaction_reference or '',
                'id': payment.id,
            }
            for payment in payments
        ]
        
        return Response({
            'success': True,
            'invoice_number': invoice.invoice_number,
            'currency': invoice.currency,
            'payments': payment_list,
            'total_paid': float(invoice.amount_paid),
            'total_due': float(invoice.amount_due),
        })
    def add_line_item(self, request, pk=None):
        """Add a line item to an invoice via API."""
        invoice = self.get_object()
        
        # Only allow adding line items to draft invoices
        if invoice.status != 'draft':
            return Response(
                {'error': 'Can only add line items to draft invoices'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract data from request
        product_id = request.data.get('product')
        description = request.data.get('description', '').strip()
        quantity = request.data.get('quantity')
        unit_price = request.data.get('unit_price')
        tax_rate = request.data.get('tax_rate')
        
        # Validation
        try:
            quantity = float(quantity) if quantity else 0
            unit_price = float(unit_price) if unit_price else 0
            tax_rate = float(tax_rate) if tax_rate else 0
            
            if quantity <= 0:
                return Response(
                    {'error': 'Quantity must be greater than 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if unit_price < 0:
                return Response(
                    {'error': 'Unit price must be non-negative'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if not description and not product_id:
                return Response(
                    {'error': 'Please provide either a product or description'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid numeric values provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get tax rate
        try:
            default_tax_rate = TaxRate.objects.filter(is_default=True).first()
            if not default_tax_rate:
                default_tax_rate = TaxRate.objects.first()
        except:
            default_tax_rate = None
        
        # Create line item
        try:
            line_item = InvoiceLineItem.objects.create(
                invoice=invoice,
                product_id=product_id if product_id else None,
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                line_amount=quantity * unit_price,
                tax_rate=default_tax_rate,
                tax_amount=(quantity * unit_price) * (tax_rate / 100) if tax_rate else 0,
                line_total=(quantity * unit_price) * (1 + (tax_rate / 100)) if tax_rate else (quantity * unit_price)
            )
            
            # Recalculate invoice totals from all line items
            from django.db.models import Sum
            from decimal import Decimal as Dec
            line_items = invoice.line_items.all()
            invoice.subtotal_amount = line_items.aggregate(Sum('line_amount'))['line_amount__sum'] or Dec('0')
            invoice.vat_amount = line_items.aggregate(Sum('tax_amount'))['tax_amount__sum'] or Dec('0')
            invoice.total_amount = line_items.aggregate(Sum('line_total'))['line_total__sum'] or Dec('0')
            invoice.amount_due = invoice.total_amount - invoice.amount_paid
            invoice.save()
            
            return Response(
                {
                    'success': True,
                    'message': 'Line item added successfully',
                    'line_item': InvoiceLineItemSerializer(line_item).data,
                    'invoice_totals': {
                        'subtotal': float(invoice.subtotal_amount),
                        'tax_total': float(invoice.vat_amount),
                        'total': float(invoice.total_amount),
                        'amount_due': float(invoice.amount_due),
                    }
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {'error': f'Error adding line item: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
