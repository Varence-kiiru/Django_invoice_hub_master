from rest_framework import viewsets, permissions
from invoicing_app.payments.models import Payment
from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().order_by('-payment_date')
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['invoice', 'status', 'payment_date']
    search_fields = ['transaction_reference', 'notes']
