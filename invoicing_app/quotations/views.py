"""
REST API ViewSets for Quotations.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Quote
from .serializers import QuoteSerializer, QuoteConvertSerializer
from .services import QuoteConversionService, QuoteStatusService


class QuoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Quote CRUD operations and custom actions.

    Endpoints:
    - GET /api/v1/quotations/ - List all quotes (with filters)
    - POST /api/v1/quotations/ - Create new quote
    - GET /api/v1/quotations/{id}/ - Get quote details
    - PUT /api/v1/quotations/{id}/ - Update quote
    - DELETE /api/v1/quotations/{id}/ - Delete quote
    - POST /api/v1/quotations/{id}/mark_sent/ - Mark as sent
    - POST /api/v1/quotations/{id}/mark_accepted/ - Mark as accepted
    - POST /api/v1/quotations/{id}/reject/ - Reject quote
    - POST /api/v1/quotations/{id}/convert_to_invoice/ - Convert to invoice
    """

    queryset = Quote.objects.all().select_related("client")
    serializer_class = QuoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["quote_number", "client", "status", "quote_date"]
    search_fields = ["quote_number", "description"]

    def perform_create(self, serializer):
        """Automatically set created_by when creating a quote."""
        from .services import QuoteNumberService

        quote_number = QuoteNumberService.generate_next_number()
        instance = serializer.save(
            quote_number=quote_number, created_by=self.request.user
        )
        instance._changed_by = self.request.user
        instance.save(update_fields=[])

    def perform_update(self, serializer):
        """Capture the logged-in user for audit trail."""
        instance = serializer.save()
        instance._changed_by = self.request.user
        instance.save(update_fields=[])

    @action(detail=True, methods=["post"])
    def mark_sent(self, request, pk=None):
        """
        Transition: draft → sent
        """
        quote = self.get_object()
        if QuoteStatusService.transition_quote(quote, "sent", actor=request.user):
            serializer = self.get_serializer(quote)
            return Response(serializer.data)
        return Response(
            {"error": f"Cannot transition from {quote.status} to sent"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["post"])
    def mark_accepted(self, request, pk=None):
        """
        Transition: viewed → accepted
        """
        quote = self.get_object()
        if QuoteStatusService.transition_quote(quote, "accepted", actor=request.user):
            serializer = self.get_serializer(quote)
            return Response(serializer.data)
        return Response(
            {"error": f"Cannot transition from {quote.status} to accepted"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        """
        Transition: any → rejected
        """
        quote = self.get_object()
        reason = request.data.get("reason", "")

        if QuoteStatusService.transition_quote(
            quote, "rejected", actor=request.user, reason=reason
        ):
            serializer = self.get_serializer(quote)
            return Response(serializer.data)
        return Response(
            {"error": f"Cannot reject {quote.status} quote"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["post"])
    def convert_to_invoice(self, request, pk=None):
        """
        Convert accepted quote → invoice

        Request body:
        {
            "invoice_date": "2026-02-21",
            "due_date": "2026-03-21"
        }
        """
        quote = self.get_object()
        serializer = QuoteConvertSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            invoice = QuoteConversionService.convert_quote_to_invoice(
                quote,
                invoice_date=serializer.validated_data.get("invoice_date"),
                due_date=serializer.validated_data["due_date"],
            )
            return Response(
                {
                    "success": True,
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                }
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
