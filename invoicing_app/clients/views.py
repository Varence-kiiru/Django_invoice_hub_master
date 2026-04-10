from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from rest_framework import viewsets, permissions
from invoicing_app.clients.models import Client
from invoicing_app.core.permissions import IsAccountant
from .serializers import ClientSerializer
from .forms import ClientForm


class ClientViewSet(viewsets.ModelViewSet):
    """Client management with role-based access control."""

    queryset = Client.objects.all().order_by("-created_at")
    serializer_class = ClientSerializer
    filterset_fields = ["name", "tax_id", "currency"]
    search_fields = ["name", "email", "tax_id"]

    def get_permissions(self):
        """
        Allow authenticated users to read clients (for invoice creation).
        Only accountants/admins can create, update, or delete.
        """
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            # All authenticated users can read client data
            return [permissions.IsAuthenticated()]
        else:
            # Only accountants can modify
            return [permissions.IsAuthenticated(), IsAccountant()]

    def get_queryset(self):
        """Filter clients based on user permissions."""
        from invoicing_app.core.permissions import user_has_permission

        user = self.request.user
        # Users with manage_clients permission see all
        if user_has_permission(user, "manage_clients"):
            return Client.objects.all().order_by("-created_at")
        # Regular users see all active clients (for invoice creation)
        return Client.objects.filter(is_active=True).order_by("-created_at")

    def perform_create(self, serializer):
        """Capture the logged-in user for audit trail."""
        instance = serializer.save()
        instance._changed_by = self.request.user
        instance.save(update_fields=[])

    def perform_update(self, serializer):
        """Capture the logged-in user for audit trail."""
        instance = serializer.save()
        instance._changed_by = self.request.user
        instance.save(update_fields=[])
        return Client.objects.filter(is_active=True).order_by("-created_at")


@login_required
def client_edit(request, pk):
    """Edit client with form validation and success messages."""
    client = get_object_or_404(Client, id=pk)

    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            try:
                with transaction.atomic():
                    client = form.save(commit=False)
                    client.save()
                    messages.success(
                        request,
                        f'Client "{client.name}" has been updated successfully.',
                    )
                    return redirect("clients:detail", pk=client.id)
            except Exception as e:
                messages.error(request, f"Error updating client: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ClientForm(instance=client)

    # Get company settings for currency display
    from invoicing_app.core.models import CompanySettings

    company_settings = CompanySettings.get_settings()

    return render(
        request,
        "4_clients/clients_edit.html",
        {"form": form, "client": client, "company_settings": company_settings},
    )
