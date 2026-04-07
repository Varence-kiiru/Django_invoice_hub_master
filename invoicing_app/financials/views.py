"""
Views for financial tracking API endpoints.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from invoicing_app.organizations.views_billing import get_user_organization
from invoicing_app.financials.models import (
    FinancialPeriod,
    RevenueCollection,
    TaxLiability,
)
from invoicing_app.financials.serializers import (
    FinancialPeriodSerializer,
    RevenueCollectionSerializer,
    TaxLiabilitySerializer,
)


class FinancialPeriodViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for financial periods - list and retrieve only."""

    permission_classes = [IsAuthenticated]
    serializer_class = FinancialPeriodSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["period_type"]
    ordering_fields = ["start_date", "end_date"]
    ordering = ["-start_date"]

    def get_queryset(self):
        """Filter periods by user's organization."""
        organization = get_user_organization(self.request.user)
        if not organization:
            return FinancialPeriod.objects.none()
        return FinancialPeriod.objects.filter(organization=organization).select_related(
            "organization"
        )

    @action(detail=False, methods=["get"])
    def current_period(self, request):
        """Get current financial period."""
        organization = get_user_organization(request.user)
        if not organization:
            return Response(
                {"detail": "No organization found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        today = timezone.now().date()
        period = FinancialPeriod.objects.filter(
            organization=organization,
            start_date__lte=today,
            end_date__gte=today,
        ).first()

        if period:
            serializer = self.get_serializer(period)
            return Response(serializer.data)
        return Response(
            {"detail": "No current period found"}, status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get financial summary for all periods."""
        organization = get_user_organization(request.user)
        if not organization:
            return Response(
                {"detail": "No organization found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        periods = FinancialPeriod.objects.filter(organization=organization)

        summary = {
            "total_revenue": 0,
            "total_tax_collected": 0,
            "pending_tax": 0,
            "remitted_tax": 0,
            "overdue_tax": 0,
            "periods": [str(p) for p in periods],
        }

        for period in periods:
            liabilities = period.taxliability_set.all()
            summary["total_revenue"] += sum(float(l.total_revenue) for l in liabilities)
            summary["total_tax_collected"] += sum(
                float(l.total_tax_collected) for l in liabilities
            )
            summary["pending_tax"] += sum(
                float(l.total_tax_collected)
                for l in liabilities
                if l.status == "pending"
            )
            summary["remitted_tax"] += sum(
                float(l.total_tax_collected)
                for l in liabilities
                if l.status == "remitted"
            )
            summary["overdue_tax"] += sum(
                float(l.total_tax_collected)
                for l in liabilities
                if l.status == "overdue"
            )

        return Response(summary)


class RevenueCollectionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for revenue collections - list and retrieve only."""

    permission_classes = [IsAuthenticated]
    serializer_class = RevenueCollectionSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["invoice__invoice_number", "payment__receipt_number"]
    ordering_fields = ["collected_date", "revenue_amount"]
    ordering = ["-collected_date"]

    def get_queryset(self):
        """Filter collections by user's organization."""
        organization = get_user_organization(self.request.user)
        if not organization:
            return RevenueCollection.objects.none()
        return RevenueCollection.objects.filter(
            organization=organization
        ).select_related("invoice", "payment", "financial_period")

    @action(detail=False, methods=["get"])
    def by_period(self, request):
        """Get revenue collections grouped by financial period."""
        organization = get_user_organization(request.user)
        if not organization:
            return Response(
                {"detail": "No organization found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        period_id = request.query_params.get("period_id")

        if not period_id:
            return Response(
                {"detail": "period_id parameter required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        collections = RevenueCollection.objects.filter(
            organization=organization,
            financial_period_id=period_id,
        ).order_by("-collected_date")

        serializer = self.get_serializer(collections, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def by_tax_type(self, request):
        """Get revenue collections grouped by tax type."""
        organization = get_user_organization(request.user)
        if not organization:
            return Response(
                {"detail": "No organization found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        period_id = request.query_params.get("period_id")

        queryset = RevenueCollection.objects.filter(organization=organization)

        if period_id:
            queryset = queryset.filter(financial_period_id=period_id)

        grouped = {}
        for collection in queryset:
            tax_type = collection.tax_type
            if tax_type not in grouped:
                grouped[tax_type] = {
                    "tax_type": tax_type,
                    "total_revenue": 0,
                    "total_tax": 0,
                    "collections": [],
                }
            grouped[tax_type]["total_revenue"] += float(collection.revenue_amount)
            grouped[tax_type]["total_tax"] += float(collection.tax_amount)
            grouped[tax_type]["collections"].append(
                RevenueCollectionSerializer(collection).data
            )

        return Response(list(grouped.values()))

    @action(detail=False, methods=["get"])
    def pending_remittance(self, request):
        """Get revenue collections pending remittance."""
        organization = get_user_organization(request.user)
        if not organization:
            return Response(
                {"detail": "No organization found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        collections = RevenueCollection.objects.filter(
            organization=organization,
            status="collected",
        ).order_by("collected_date")

        serializer = self.get_serializer(collections, many=True)
        return Response(serializer.data)


class TaxLiabilityViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for tax liabilities - list and retrieve only."""

    permission_classes = [IsAuthenticated]
    serializer_class = TaxLiabilitySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["tax_type"]
    ordering_fields = ["due_date", "total_tax_collected"]
    ordering = ["due_date"]

    def get_queryset(self):
        """Filter liabilities by user's organization."""
        organization = get_user_organization(self.request.user)
        if not organization:
            return TaxLiability.objects.none()
        return TaxLiability.objects.filter(organization=organization).select_related(
            "financial_period", "organization"
        )

    @action(detail=False, methods=["get"])
    def overdue(self, request):
        """Get overdue tax liabilities."""
        organization = get_user_organization(request.user)
        if not organization:
            return Response(
                {"detail": "No organization found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        today = timezone.now().date()
        liabilities = TaxLiability.objects.filter(
            Q(status="overdue")
            | Q(due_date__lt=today, status__in=["pending", "due_soon"]),
            organization=organization,
        ).order_by("due_date")

        serializer = self.get_serializer(liabilities, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def due_soon(self, request):
        """Get tax liabilities due within 7 days."""
        organization = get_user_organization(request.user)
        if not organization:
            return Response(
                {"detail": "No organization found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        today = timezone.now().date()
        week_out = today + timedelta(days=7)
        liabilities = TaxLiability.objects.filter(
            status__in=["pending", "due_soon"],
            due_date__range=[today, week_out],
            organization=organization,
        ).order_by("due_date")

        serializer = self.get_serializer(liabilities, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get tax liability summary."""
        organization = get_user_organization(request.user)
        if not organization:
            return Response(
                {"detail": "No organization found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        liabilities = TaxLiability.objects.filter(organization=organization)

        summary = {
            "total_pending": 0,
            "total_due_soon": 0,
            "total_overdue": 0,
            "total_remitted": 0,
            "total_tax_collected": 0,
            "by_tax_type": {},
        }

        for liability in liabilities:
            tax_amount = float(liability.total_tax_collected)
            summary["total_tax_collected"] += tax_amount

            if liability.status == "pending":
                summary["total_pending"] += tax_amount
            elif liability.status == "due_soon":
                summary["total_due_soon"] += tax_amount
            elif liability.status == "overdue":
                summary["total_overdue"] += tax_amount
            elif liability.status == "remitted":
                summary["total_remitted"] += tax_amount

            if liability.tax_type not in summary["by_tax_type"]:
                summary["by_tax_type"][liability.tax_type] = {
                    "tax_type": liability.tax_type,
                    "total": 0,
                    "status_breakdown": {
                        "pending": 0,
                        "due_soon": 0,
                        "overdue": 0,
                        "remitted": 0,
                    },
                }

            summary["by_tax_type"][liability.tax_type]["total"] += tax_amount
            summary["by_tax_type"][liability.tax_type]["status_breakdown"][
                liability.status
            ] += tax_amount

        return Response(summary)

    @action(detail=True, methods=["post"])
    def mark_remitted(self, request, pk=None):
        """Mark a tax liability as remitted."""
        liability = self.get_object()
        organization = get_user_organization(request.user)

        if liability.organization != organization:
            return Response(
                {"detail": "Not authorized"},
                status=status.HTTP_403_FORBIDDEN,
            )

        liability.status = "remitted"
        liability.remitted_date = timezone.now().date()
        liability.remittance_reference = request.data.get("remittance_reference", "")
        liability.save()

        serializer = self.get_serializer(liability)
        return Response(serializer.data)
