"""
Advanced search and filtering utilities for the invoicing application.

Provides helpers for:
- Building complex queries from filter criteria
- Full-text search across multiple fields
- Date range filtering
- Saved filter management
- Query optimization
"""

from django.db.models import Q, F, Value
from django.utils import timezone
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AdvancedFilterBuilder:
    """Builder for constructing complex query filters."""
    
    @staticmethod
    def apply_invoice_filters(queryset, criteria):
        """
        Apply advanced filters to invoice queryset.
        
        Supported criteria:
        - status: single or list of statuses
        - min_amount, max_amount: amount range
        - client_name: partial client name match
        - invoice_number: exact invoice number
        - from_date, to_date: invoice date range
        - days_overdue: minimum days overdue
        - amount_due_gt: amount due greater than
        """
        q_filter = Q()
        
        # Status filter
        if 'status' in criteria:
            status = criteria['status']
            if isinstance(status, list):
                q_filter &= Q(status__in=status)
            else:
                q_filter &= Q(status=status)
        
        # Amount range
        if 'min_amount' in criteria:
            try:
                q_filter &= Q(total_amount__gte=float(criteria['min_amount']))
            except (ValueError, TypeError):
                pass
        
        if 'max_amount' in criteria:
            try:
                q_filter &= Q(total_amount__lte=float(criteria['max_amount']))
            except (ValueError, TypeError):
                pass
        
        # Client name search
        if 'client_name' in criteria and criteria['client_name'].strip():
            q_filter &= Q(client__name__icontains=criteria['client_name'].strip())
        
        # Invoice number
        if 'invoice_number' in criteria and criteria['invoice_number'].strip():
            q_filter &= Q(invoice_number__icontains=criteria['invoice_number'].strip())
        
        # Date range filters
        if 'from_date' in criteria:
            try:
                from_date = datetime.strptime(criteria['from_date'], '%Y-%m-%d').date()
                q_filter &= Q(invoice_date__gte=from_date)
            except (ValueError, TypeError):
                pass
        
        if 'to_date' in criteria:
            try:
                to_date = datetime.strptime(criteria['to_date'], '%Y-%m-%d').date()
                q_filter &= Q(invoice_date__lte=to_date)
            except (ValueError, TypeError):
                pass
        
        # Overdue check
        if 'days_overdue' in criteria:
            try:
                days = int(criteria['days_overdue'])
                cutoff_date = timezone.now().date() - timedelta(days=days)
                q_filter &= Q(due_date__lt=cutoff_date, status__in=['issued', 'sent'])
            except (ValueError, TypeError):
                pass
        
        # Amount due filter
        if 'amount_due_gt' in criteria:
            try:
                amount = float(criteria['amount_due_gt'])
                q_filter &= Q(amount_due__gt=amount)
            except (ValueError, TypeError):
                pass
        
        return queryset.filter(q_filter)
    
    @staticmethod
    def apply_payment_filters(queryset, criteria):
        """
        Apply advanced filters to payment queryset.
        
        Supported criteria:
        - status: single or list of payment statuses
        - method: payment method filter
        - min_amount, max_amount: amount range
        - from_date, to_date: payment date range
        - invoice_number: filter by invoice number
        - client_name: filter by client name
        """
        q_filter = Q()
        
        # Status filter
        if 'status' in criteria:
            status = criteria['status']
            if isinstance(status, list):
                q_filter &= Q(status__in=status)
            else:
                q_filter &= Q(status=status)
        
        # Payment method
        if 'method' in criteria and criteria['method']:
            q_filter &= Q(payment_method__name=criteria['method'])
        
        # Amount range
        if 'min_amount' in criteria:
            try:
                q_filter &= Q(amount__gte=float(criteria['min_amount']))
            except (ValueError, TypeError):
                pass
        
        if 'max_amount' in criteria:
            try:
                q_filter &= Q(amount__lte=float(criteria['max_amount']))
            except (ValueError, TypeError):
                pass
        
        # Date range
        if 'from_date' in criteria:
            try:
                from_date = datetime.strptime(criteria['from_date'], '%Y-%m-%d').date()
                q_filter &= Q(payment_date__gte=from_date)
            except (ValueError, TypeError):
                pass
        
        if 'to_date' in criteria:
            try:
                to_date = datetime.strptime(criteria['to_date'], '%Y-%m-%d').date()
                q_filter &= Q(payment_date__lte=to_date)
            except (ValueError, TypeError):
                pass
        
        # Invoice-related filters
        if 'invoice_number' in criteria and criteria['invoice_number'].strip():
            q_filter &= Q(invoice__invoice_number__icontains=criteria['invoice_number'].strip())
        
        if 'client_name' in criteria and criteria['client_name'].strip():
            q_filter &= Q(invoice__client__name__icontains=criteria['client_name'].strip())
        
        return queryset.filter(q_filter)
    
    @staticmethod
    def apply_client_filters(queryset, criteria):
        """
        Apply advanced filters to client queryset.
        
        Supported criteria:
        - name: client name search
        - email: email search
        - client_type: business or personal
        - is_active: active status
        - has_invoices: only clients with invoices
        """
        q_filter = Q()
        
        # Name search
        if 'name' in criteria and criteria['name'].strip():
            q_filter &= Q(name__icontains=criteria['name'].strip())
        
        # Email search
        if 'email' in criteria and criteria['email'].strip():
            q_filter &= Q(email__icontains=criteria['email'].strip())
        
        # Client type
        if 'client_type' in criteria and criteria['client_type']:
            q_filter &= Q(client_type=criteria['client_type'])
        
        # Active status
        if 'is_active' in criteria:
            is_active = criteria['is_active']
            if isinstance(is_active, str):
                is_active = is_active.lower() == 'true'
            q_filter &= Q(is_active=is_active)
        
        # Has invoices
        if 'has_invoices' in criteria:
            has_invoices = criteria['has_invoices']
            if isinstance(has_invoices, str):
                has_invoices = has_invoices.lower() == 'true'
            if has_invoices:
                q_filter &= Q(invoices__isnull=False)
            else:
                q_filter &= Q(invoices__isnull=True)
        
        return queryset.filter(q_filter).distinct()
    
    @staticmethod
    def apply_quotation_filters(queryset, criteria):
        """
        Apply advanced filters to quotation queryset.
        
        Supported criteria:
        - status: single or list of quote statuses
        - min_amount, max_amount: amount range
        - client_name: partial client name match
        - quote_number: exact quote number
        - from_date, to_date: quote date range
        - valid_until_from, valid_until_to: quote expiration range
        - is_expired: filter by expiration status
        """
        q_filter = Q()
        
        # Status filter
        if 'status' in criteria:
            status = criteria['status']
            if isinstance(status, list):
                q_filter &= Q(status__in=status)
            else:
                q_filter &= Q(status=status)
        
        # Amount range
        if 'min_amount' in criteria:
            try:
                q_filter &= Q(total_amount__gte=float(criteria['min_amount']))
            except (ValueError, TypeError):
                pass
        
        if 'max_amount' in criteria:
            try:
                q_filter &= Q(total_amount__lte=float(criteria['max_amount']))
            except (ValueError, TypeError):
                pass
        
        # Client name search
        if 'client_name' in criteria and criteria['client_name'].strip():
            q_filter &= Q(client__name__icontains=criteria['client_name'].strip())
        
        # Quote number
        if 'quote_number' in criteria and criteria['quote_number'].strip():
            q_filter &= Q(quote_number__icontains=criteria['quote_number'].strip())
        
        # Date range filters (quote date)
        if 'from_date' in criteria:
            try:
                from_date = datetime.strptime(criteria['from_date'], '%Y-%m-%d').date()
                q_filter &= Q(quote_date__gte=from_date)
            except (ValueError, TypeError):
                pass
        
        if 'to_date' in criteria:
            try:
                to_date = datetime.strptime(criteria['to_date'], '%Y-%m-%d').date()
                q_filter &= Q(quote_date__lte=to_date)
            except (ValueError, TypeError):
                pass
        
        # Valid until range filters
        if 'valid_until_from' in criteria:
            try:
                valid_from = datetime.strptime(criteria['valid_until_from'], '%Y-%m-%d').date()
                q_filter &= Q(valid_until__gte=valid_from)
            except (ValueError, TypeError):
                pass
        
        if 'valid_until_to' in criteria:
            try:
                valid_to = datetime.strptime(criteria['valid_until_to'], '%Y-%m-%d').date()
                q_filter &= Q(valid_until__lte=valid_to)
            except (ValueError, TypeError):
                pass
        
        # Expiration status
        if 'is_expired' in criteria:
            is_expired = criteria['is_expired']
            if isinstance(is_expired, str):
                is_expired = is_expired.lower() == 'true'
            if is_expired:
                q_filter &= Q(valid_until__lt=timezone.now().date())
            else:
                q_filter &= Q(valid_until__gte=timezone.now().date())
        
        return queryset.filter(q_filter)


class FullTextSearch:
    """Full-text search utilities."""
    
    @staticmethod
    def search_invoices(queryset, query):
        """
        Full-text search across invoices.
        Searches: invoice_number, client name, description, line item description
        """
        if not query or not query.strip():
            return queryset
        
        # Clean search query
        query = query.strip()
        
        return queryset.filter(
            Q(invoice_number__icontains=query) |
            Q(client__name__icontains=query) |
            Q(description__icontains=query) |
            Q(line_items__description__icontains=query)
        ).distinct()
    
    @staticmethod
    def search_payments(queryset, query):
        """Full-text search across payments."""
        if not query or not query.strip():
            return queryset
        
        query = query.strip()
        
        return queryset.filter(
            Q(receipt_number__icontains=query) |
            Q(invoice__invoice_number__icontains=query) |
            Q(invoice__client__name__icontains=query) |
            Q(notes__icontains=query)
        ).distinct()
    
    @staticmethod
    def search_clients(queryset, query):
        """Full-text search across clients."""
        if not query or not query.strip():
            return queryset
        
        query = query.strip()
        
        return queryset.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query) |
            Q(tax_id__icontains=query)
        ).distinct()
    
    @staticmethod
    def search_quotations(queryset, query):
        """Full-text search across quotations."""
        if not query or not query.strip():
            return queryset
        
        query = query.strip()
        
        return queryset.filter(
            Q(quote_number__icontains=query) |
            Q(client__name__icontains=query) |
            Q(description__icontains=query) |
            Q(line_items__description__icontains=query)
        ).distinct()


class FilterPreset:
    """Preset filter management."""
    
    @staticmethod
    def save_filter(name, description, filter_type, criteria, user, is_global=False, sort_by=None):
        """Save a filter preset."""
        from invoicing_app.core.models import SavedFilter
        
        saved_filter = SavedFilter.objects.create(
            name=name,
            description=description,
            filter_type=filter_type,
            filter_criteria=criteria,
            created_by=user,
            is_global=is_global,
            sort_by=sort_by
        )
        return saved_filter
    
    @staticmethod
    def get_user_filters(user, filter_type):
        """Get available filters for a user."""
        from invoicing_app.core.models import SavedFilter
        return SavedFilter.get_user_filters(user, filter_type)
    
    @staticmethod
    def apply_saved_filter(queryset, saved_filter, model_type):
        """Apply a saved filter to a queryset."""
        if model_type == 'invoice':
            return AdvancedFilterBuilder.apply_invoice_filters(
                queryset, saved_filter.filter_criteria
            )
        elif model_type == 'payment':
            return AdvancedFilterBuilder.apply_payment_filters(
                queryset, saved_filter.filter_criteria
            )
        elif model_type == 'client':
            return AdvancedFilterBuilder.apply_client_filters(
                queryset, saved_filter.filter_criteria
            )
        elif model_type == 'quotation':
            return AdvancedFilterBuilder.apply_quotation_filters(
                queryset, saved_filter.filter_criteria
            )
        return queryset


def get_filter_options(filter_type):
    """Get available filter options for a given type."""
    options = {
        'invoice': {
            'statuses': ['draft', 'sent', 'issued', 'paid', 'partially_paid', 'overdue', 'cancelled'],
            'date_ranges': ['today', 'this_week', 'this_month', 'last_30_days', 'custom'],
            'common_filters': [
                {'name': 'Unpaid', 'criteria': {'status': ['issued', 'sent'], 'amount_due_gt': 0}},
                {'name': 'Overdue', 'criteria': {'status': 'overdue'}},
                {'name': 'Draft', 'criteria': {'status': 'draft'}},
                {'name': 'This Month', 'criteria': {'from_date': timezone.now().replace(day=1)}},
            ]
        },
        'payment': {
            'statuses': ['pending', 'successful', 'failed', 'refunded'],
            'methods': ['cash', 'bank_transfer', 'card', 'check', 'mobile_money'],
            'date_ranges': ['today', 'this_week', 'this_month', 'custom'],
        },
        'client': {
            'types': ['business', 'individual'],
            'statuses': ['active', 'inactive'],
            'common_filters': [
                {'name': 'Active Business', 'criteria': {'is_active': True, 'client_type': 'business'}},
                {'name': 'With Invoices', 'criteria': {'has_invoices': True}},
            ]
        },
        'quotation': {
            'statuses': ['draft', 'issued', 'sent', 'viewed', 'accepted', 'rejected', 'expired', 'converted', 'archived'],
            'date_ranges': ['today', 'this_week', 'this_month', 'custom'],
            'common_filters': [
                {'name': 'Accepted', 'criteria': {'status': 'accepted'}},
                {'name': 'Expired', 'criteria': {'is_expired': True}},
                {'name': 'Draft', 'criteria': {'status': 'draft'}},
                {'name': 'Converted', 'criteria': {'status': 'converted'}},
            ]
        },
    }
    return options.get(filter_type, {})


def parse_url_filters(request_get):
    """Parse URL query parameters into filter criteria."""
    criteria = {}
    
    # Standard filters
    for key in ['status', 'method', 'client_type', 'client_name', 'invoice_number', 'quote_number', 'email', 'name']:
        if key in request_get:
            criteria[key] = request_get.get(key)
    
    # Amount filters
    if 'min_amount' in request_get:
        criteria['min_amount'] = request_get.get('min_amount')
    if 'max_amount' in request_get:
        criteria['max_amount'] = request_get.get('max_amount')
    
    # Date filters
    if 'from_date' in request_get:
        criteria['from_date'] = request_get.get('from_date')
    if 'to_date' in request_get:
        criteria['to_date'] = request_get.get('to_date')
    
    # Quote-specific date filters
    if 'valid_until_from' in request_get:
        criteria['valid_until_from'] = request_get.get('valid_until_from')
    if 'valid_until_to' in request_get:
        criteria['valid_until_to'] = request_get.get('valid_until_to')
    
    # Boolean filters
    for key in ['is_active', 'has_invoices', 'is_expired']:
        if key in request_get:
            criteria[key] = request_get.get(key).lower() == 'true'
    
    # Remove empty values
    criteria = {k: v for k, v in criteria.items() if v}
    
    return criteria
