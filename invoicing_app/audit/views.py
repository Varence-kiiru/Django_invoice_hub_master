from rest_framework import viewsets, permissions
from invoicing_app.audit.models import InvoiceSnapshot, AuditLog
from invoicing_app.core.permissions import CanViewInvoices, CanViewAuditLogs
from .serializers import InvoiceSnapshotSerializer, AuditLogSerializer


class InvoiceSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    """Invoice snapshot view - read-only with role-based access."""
    queryset = InvoiceSnapshot.objects.all().order_by('-snapshot_date')
    serializer_class = InvoiceSnapshotSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewInvoices]
    filterset_fields = ['invoice', 'is_kra_verified']
    search_fields = ['invoice_number']
    
    def get_queryset(self):
        """Filter snapshots based on user role and invoice ownership."""
        user = self.request.user
        try:
            profile = user.invoicing_profile
            # Admins and accountants see all snapshots
            if profile.role in ['admin', 'accountant']:
                return InvoiceSnapshot.objects.all().order_by('-snapshot_date')
            # Regular users see only snapshots for their invoices
            if profile.role == 'user':
                return InvoiceSnapshot.objects.filter(
                    invoice__created_by=user
                ).order_by('-snapshot_date')
        except:
            pass
        return InvoiceSnapshot.objects.none()


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Audit log view - accountants and admins only (read-only)."""
    queryset = AuditLog.objects.all().order_by('-timestamp')
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewAuditLogs]
    filterset_fields = ['entity_type', 'action']
    search_fields = ['entity_type', 'actor__email', 'notes']
