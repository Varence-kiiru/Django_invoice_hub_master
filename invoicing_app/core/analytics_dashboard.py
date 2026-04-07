"""
Enhanced dashboard analytics and metrics.
Provides comprehensive financial data and insights for the dashboard.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from invoicing_app.invoices.models import Invoice
from invoicing_app.payments.models import Payment
from invoicing_app.clients.models import Client
from invoicing_app.quotations.models import Quote


class DashboardAnalytics:
    """Analytics and metrics for dashboard"""

    def __init__(self, user=None):
        self.user = user

    def get_summary_metrics(self):
        """Get key summary metrics"""
        return {
            "total_invoices": Invoice.objects.count(),
            "total_clients": Client.objects.count(),
            "total_quotations": Quote.objects.count(),
            "active_clients": Client.objects.filter(is_active=True).count(),
        }

    def get_financial_metrics(self):
        """Get financial metrics"""
        invoices = Invoice.objects.all()
        payments = Payment.objects.all()

        total_invoiced = invoices.aggregate(Sum("total_amount"))[
            "total_amount__sum"
        ] or Decimal("0")
        total_paid = payments.aggregate(Sum("amount"))["amount__sum"] or Decimal("0")
        outstanding = total_invoiced - total_paid

        invoice_count = invoices.count()
        paid_invoices = payments.count()
        avg_transaction = invoices.aggregate(Avg("total_amount"))[
            "total_amount__avg"
        ] or Decimal("0")

        # Calculate percentages
        ar_percentage = (
            (outstanding / total_invoiced * 100) if total_invoiced > 0 else 0
        )
        payment_rate = (total_paid / total_invoiced) if total_invoiced > 0 else 0

        return {
            "total_revenue": float(total_invoiced),
            "revenue_change_percent": 0,  # Would need historical data for comparison
            "outstanding_ar": float(outstanding),
            "ar_percentage": float(ar_percentage),
            "average_transaction": float(avg_transaction),
            "invoice_count": invoice_count,
            "payment_rate": float(payment_rate),
            "paid_invoices": paid_invoices,
        }

    def get_invoice_metrics(self):
        """Get invoice-specific metrics"""
        invoices = Invoice.objects.all()

        return {
            "total_count": invoices.count(),
            "by_status": dict(
                invoices.values("status")
                .annotate(count=Count("id"))
                .values_list("status", "count")
            ),
            "overdue_count": invoices.filter(
                Q(status="overdue")
                | Q(due_date__lt=timezone.now().date(), status__in=["sent", "issued"])
            ).count(),
            "this_month": invoices.filter(
                created_at__gte=timezone.now().replace(day=1)
            ).count(),
            "average_value": float(
                invoices.aggregate(Avg("total_amount"))["total_amount__avg"] or 0
            ),
        }

    def get_payment_metrics(self):
        """Get payment-specific metrics"""
        payments = Payment.objects.all()

        return {
            "total_count": payments.count(),
            "by_status": dict(
                payments.values("status")
                .annotate(count=Count("id"))
                .values_list("status", "count")
            ),
            "this_month": payments.filter(
                payment_date__gte=timezone.now().replace(day=1)
            ).count(),
            "average_transaction": float(
                payments.aggregate(Avg("amount"))["amount__avg"] or 0
            ),
        }

    def get_quotation_metrics(self):
        """Get quotation-specific metrics"""
        quotations = Quote.objects.all()

        return {
            "total_count": quotations.count(),
            "by_status": dict(
                quotations.values("status")
                .annotate(count=Count("id"))
                .values_list("status", "count")
            ),
            "conversion_rate": self._calculate_conversion_rate(),
            "average_value": float(
                quotations.aggregate(Avg("total_amount"))["total_amount__avg"] or 0
            ),
        }

    def get_client_metrics(self):
        """Get client-specific metrics"""
        clients = Client.objects.all()

        return {
            "total_count": clients.count(),
            "active_count": clients.filter(is_active=True).count(),
            "inactive_count": clients.filter(is_active=False).count(),
            "with_outstanding": clients.filter(outstanding_amount__gt=0).count(),
        }

    def get_timeline_data(self, days=30):
        """Get timeline data for charts"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        # Daily invoice totals
        daily_invoices = {}
        for i in range(days):
            date = start_date + timedelta(days=i)
            amount = Invoice.objects.filter(created_at__date=date).aggregate(
                Sum("total_amount")
            )["total_amount__sum"] or Decimal("0")
            daily_invoices[date.isoformat()] = float(amount)

        # Daily payment totals
        daily_payments = {}
        for i in range(days):
            date = start_date + timedelta(days=i)
            amount = Payment.objects.filter(payment_date=date).aggregate(Sum("amount"))[
                "amount__sum"
            ] or Decimal("0")
            daily_payments[date.isoformat()] = float(amount)

        return {
            "daily_invoices": daily_invoices,
            "daily_payments": daily_payments,
            "period_days": days,
        }

    def get_top_clients(self, limit=5):
        """Get top clients by invoice value"""
        clients = Client.objects.annotate(
            total_invoiced=Sum("invoices__total_amount"),
            invoice_count=Count("invoices"),
        ).order_by("-total_invoiced")[:limit]

        result = []
        for client in clients:
            total_invoiced = client.total_invoiced or Decimal("0")
            invoice_count = client.invoice_count or 0

            # Get total payments for this client from their invoices
            total_paid = Payment.objects.filter(invoice__client=client).aggregate(
                Sum("amount")
            )["amount__sum"] or Decimal("0")

            # Calculate metrics
            average_invoice = float(
                (total_invoiced / invoice_count) if invoice_count > 0 else 0
            )
            payment_rate = float(
                (total_paid / total_invoiced) if total_invoiced > 0 else 0
            )

            result.append(
                {
                    "id": client.id,
                    "name": client.name,
                    "email": client.email or "",
                    "total_revenue": float(total_invoiced),
                    "invoice_count": invoice_count,
                    "average_invoice": average_invoice,
                    "payment_rate": payment_rate,
                }
            )

        return result

    def get_payment_method_breakdown(self):
        """Get payment breakdown by method"""
        from invoicing_app.payments.models import PaymentMethod

        methods = PaymentMethod.objects.annotate(
            total_amount=Sum("payments__amount"), count=Count("payments", distinct=True)
        ).filter(count__gt=0)

        return {
            "methods": [
                {
                    "method_name": method.name,
                    "amount": float(method.total_amount or 0),
                    "count": method.count or 0,
                }
                for method in methods
            ]
        }

    def get_aging_report(self):
        """Get accounts receivable aging"""
        today = timezone.now().date()

        invoices = Invoice.objects.filter(status__in=["sent", "issued", "overdue"])

        return {
            "current": invoices.filter(due_date__gte=today).count(),
            "30_days": invoices.filter(
                due_date__gte=today - timedelta(days=30), due_date__lt=today
            ).count(),
            "60_days": invoices.filter(
                due_date__gte=today - timedelta(days=60),
                due_date__lt=today - timedelta(days=30),
            ).count(),
            "over_90_days": invoices.filter(
                due_date__lt=today - timedelta(days=90)
            ).count(),
        }

    def _calculate_conversion_rate(self):
        """Calculate quotation to invoice conversion rate"""
        total_quotes = Quote.objects.count()
        converted_quotes = Quote.objects.filter(status="converted").count()

        return (converted_quotes / total_quotes * 100) if total_quotes > 0 else 0


@login_required
@require_http_methods(["GET"])
def get_dashboard_data(request):
    """API endpoint for complete dashboard data"""
    try:
        analytics = DashboardAnalytics(request.user)

        return JsonResponse(
            {
                "success": True,
                "data": {
                    "summary": analytics.get_summary_metrics(),
                    "financial": analytics.get_financial_metrics(),
                    "invoices": analytics.get_invoice_metrics(),
                    "payments": analytics.get_payment_metrics(),
                    "quotations": analytics.get_quotation_metrics(),
                    "clients": analytics.get_client_metrics(),
                    "timeline": analytics.get_timeline_data(30),
                    "top_clients": analytics.get_top_clients(5),
                    "payment_methods": analytics.get_payment_method_breakdown(),
                    "aging": analytics.get_aging_report(),
                },
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_financial_metrics(request):
    """API endpoint for financial metrics only"""
    from invoicing_app.core.models import CompanySettings

    analytics = DashboardAnalytics(request.user)
    settings = CompanySettings.objects.first()

    return JsonResponse(
        {
            "success": True,
            "data": {
                **analytics.get_financial_metrics(),
                "currency_code": settings.default_currency if settings else "KES",
                "currency_symbol": settings.currency_symbol if settings else "KES",
            },
        }
    )


@login_required
@require_http_methods(["GET"])
def get_timeline_chart(request):
    """API endpoint for timeline chart data"""
    days = int(request.GET.get("days", 30))
    analytics = DashboardAnalytics(request.user)

    return JsonResponse(
        {"success": True, "data": analytics.get_timeline_data(min(days, 365))}
    )


@login_required
@require_http_methods(["GET"])
def get_aging_report(request):
    """API endpoint for aging report"""
    analytics = DashboardAnalytics(request.user)

    return JsonResponse({"success": True, "data": analytics.get_aging_report()})


@login_required
@require_http_methods(["GET"])
def get_payment_method_breakdown(request):
    """API endpoint for payment method breakdown"""
    analytics = DashboardAnalytics(request.user)

    return JsonResponse(
        {"success": True, "data": analytics.get_payment_method_breakdown()}
    )


@login_required
@require_http_methods(["GET"])
def get_top_clients(request):
    """API endpoint for top clients"""
    analytics = DashboardAnalytics(request.user)
    limit = int(request.GET.get("limit", 10))

    return JsonResponse(
        {"success": True, "data": analytics.get_top_clients(limit=limit)}
    )
