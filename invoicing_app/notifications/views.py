from rest_framework import viewsets, permissions
from invoicing_app.notifications.models import EmailTemplate, NotificationLog
from invoicing_app.core.permissions import IsAccountant, CanViewAuditLogs
from .serializers import EmailTemplateSerializer, NotificationLogSerializer


class EmailTemplateViewSet(viewsets.ModelViewSet):
    """Email template management - accountants and admins only."""
    queryset = EmailTemplate.objects.all().order_by('name')
    serializer_class = EmailTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountant]
    filterset_fields = ['is_active']
    search_fields = ['name', 'subject']


class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Notification log view - accountants and admins only (read-only)."""
    queryset = NotificationLog.objects.all().order_by('-created_at')
    serializer_class = NotificationLogSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewAuditLogs]
    filterset_fields = ['entity_type', 'notification_type', 'status']
    search_fields = ['recipient', 'entity_type', 'notification_type']
