from rest_framework import serializers
from invoicing_app.notifications.models import EmailTemplate, NotificationLog


class EmailTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for email templates.
    """

    class Meta:
        model = EmailTemplate
        fields = [
            "id",
            "name",
            "subject",
            "body",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class NotificationLogSerializer(serializers.ModelSerializer):
    """
    Serializer for notification log entries.
    """

    class Meta:
        model = NotificationLog
        fields = [
            "id",
            "entity_type",
            "entity_id",
            "notification_type",
            "recipient",
            "subject",
            "status",
            "error_message",
            "sent_at",
            "created_at",
        ]
        read_only_fields = ["created_at"]
