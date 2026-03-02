"""Core views for the invoicing application."""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
def api_home(request):
    """Home endpoint providing API information and available endpoints."""
    return Response({
        'message': 'Welcome to Invoice Management API',
        'version': '1.0',
        'status': 'operational',
        'documentation': {
            'api_base': '/api/v1/',
            'admin': '/admin/',
            'authentication': '/api/v1/token/',
            'token_refresh': '/api/v1/token/refresh/',
        },
        'available_endpoints': {
            'business_logic': {
                'clients': '/api/v1/clients/',
                'products': '/api/v1/products/',
                'invoices': '/api/v1/invoices/',
                'payments': '/api/v1/payments/',
                'taxrates': '/api/v1/taxrates/',
                'vatrules': '/api/v1/vatrules/',
            },
            'user_management': {
                'roles': '/api/v1/roles/',
                'users': '/api/v1/users/',
            },
            'communication': {
                'email_templates': '/api/v1/email-templates/',
                'notifications': '/api/v1/notifications/',
            },
            'audit_and_history': {
                'invoice_snapshots': '/api/v1/invoice-snapshots/',
                'audit_logs': '/api/v1/audit-logs/',
            },
        },
        'authentication': {
            'method': 'JWT',
            'obtain_token': 'POST /api/v1/token/ with username and password',
            'refresh_token': 'POST /api/v1/token/refresh/ with refresh token',
            'headers': 'Authorization: Bearer <access_token>',
        },
    }, status=status.HTTP_200_OK)
