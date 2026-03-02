from rest_framework import serializers
from invoicing_app.audit.models import InvoiceSnapshot, AuditLog


class InvoiceSnapshotSerializer(serializers.ModelSerializer):
    """
    Serializer for immutable invoice snapshots (KRA compliance).
    Read-only after creation.
    """
    invoice_number = serializers.CharField(read_only=True)
    
    class Meta:
        model = InvoiceSnapshot
        fields = [
            'id', 'invoice', 'invoice_number', 'snapshot_date', 'snapshot_version',
            'invoice_state_json', 'kra_etims_receipt', 'is_kra_verified', 'created_at'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'snapshot_date', 'invoice_state_json',
            'kra_etims_receipt', 'is_kra_verified', 'created_at'
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for immutable audit logs (insert-only event log).
    """
    actor_email = serializers.CharField(source='actor.email', read_only=True, allow_null=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'entity_type', 'entity_id', 'action', 'old_values', 'new_values',
            'actor', 'actor_email', 'timestamp', 'ip_address', 'user_agent', 'notes',
            'is_kra_verified'
        ]
        read_only_fields = [
            'id', 'timestamp', 'is_kra_verified'
        ]
