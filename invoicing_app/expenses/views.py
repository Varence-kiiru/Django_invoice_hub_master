"""Django REST API views for expenses."""
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Expense, ExpenseCategory, Vendor
from .serializers import ExpenseSerializer, ExpenseCategorySerializer, VendorSerializer


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for expense categories."""
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class VendorViewSet(viewsets.ModelViewSet):
    """ViewSet for vendors."""
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'contact_email']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class ExpenseViewSet(viewsets.ModelViewSet):
    """ViewSet for expenses."""
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'category', 'vendor', 'expense_date', 'payment_method']
    search_fields = ['description', 'reference_number']
    ordering_fields = ['expense_date', 'amount', 'created_at', 'status']
    ordering = ['-expense_date']
