"""Core views for the invoicing application."""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework import viewsets
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for users - used for transfer ownership dropdown."""
    queryset = User.objects.all().order_by('email')
    permission_classes = [permissions.IsAuthenticated]  # Require authentication
    
    def get_queryset(self):
        # Only allow superusers or staff to see all users
        if self.request.user.is_superuser or self.request.user.is_staff:
            return User.objects.all().order_by('email')
        return User.objects.none()
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        data = []
        for user in queryset:
            data.append({
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username': user.username,
                'is_active': user.is_active,
            })
        return Response({'results': data})
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        data = []
        for user in queryset:
            data.append({
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username': user.username,
                'is_active': user.is_active,
            })
        return Response({'results': data})


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
