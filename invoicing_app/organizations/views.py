from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db import transaction
from .models import Organization, OrganizationMember, Subscription, Invoice
from .serializers import (
    OrganizationSerializer,
    OrganizationMemberSerializer,
    SubscriptionSerializer,
    InvoiceSerializer,
)


class OrganizationViewSet(viewsets.ModelViewSet):
    """
    API endpoints for organization management.
    """

    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "slug"

    def get_queryset(self):
        """Only return organizations the user is a member of"""
        user = self.request.user
        return Organization.objects.filter(
            members__user=user, is_active=True
        ).distinct()

    @action(detail=True, methods=["post"])
    def add_member(self, request, slug=None):
        """Add a new member to the organization"""
        org = self.get_object()

        # Check if user is owner/admin
        membership = org.members.filter(user=request.user).first()
        if not membership or membership.role not in ["owner", "admin"]:
            return Response(
                {"error": "Only admins can add members"},
                status=status.HTTP_403_FORBIDDEN,
            )

        email = request.data.get("email")
        role = request.data.get("role", "staff")

        if not email:
            return Response(
                {"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        member, created = OrganizationMember.objects.get_or_create(
            organization=org, user=user, defaults={"role": role}
        )

        serializer = OrganizationMemberSerializer(member)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def remove_member(self, request, slug=None):
        """Remove a member from organization"""
        org = self.get_object()

        # Check if user is owner/admin
        membership = org.members.filter(user=request.user).first()
        if not membership or membership.role not in ["owner", "admin"]:
            return Response(
                {"error": "Only admins can remove members"},
                status=status.HTTP_403_FORBIDDEN,
            )

        member_id = request.data.get("member_id")
        try:
            member = OrganizationMember.objects.get(organization=org, id=member_id)
            member.delete()
            return Response({"success": "Member removed"})
        except OrganizationMember.DoesNotExist:
            return Response(
                {"error": "Member not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=["get"])
    def members(self, request, slug=None):
        """List all members of the organization"""
        org = self.get_object()
        members = org.members.filter(is_active=True)
        serializer = OrganizationMemberSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def plan_limits(self, request, slug=None):
        """Get plan limits for this organization"""
        org = self.get_object()
        limits = org.get_plan_limits()
        return Response(limits)

    @action(detail=True, methods=["post"])
    def transfer_ownership(self, request, slug=None):
        """Transfer primary ownership to another member"""
        org = self.get_object()

        # Check if user is the current primary owner
        current_owner_membership = org.members.filter(
            user=request.user, is_primary=True
        ).first()

        if not current_owner_membership:
            return Response(
                {"error": "Only the current primary owner can transfer ownership"},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_owner_id = request.data.get("new_owner_id")
        if not new_owner_id:
            return Response(
                {"error": "New owner ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            new_owner_membership = org.members.get(id=new_owner_id, is_active=True)
        except OrganizationMember.DoesNotExist:
            return Response(
                {"error": "New owner not found in this organization"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Cannot transfer to yourself
        if new_owner_membership.user == request.user:
            return Response(
                {"error": "Cannot transfer ownership to yourself"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Transfer ownership
        with transaction.atomic():
            # Remove primary status from current owner
            current_owner_membership.is_primary = False
            current_owner_membership.save()

            # Remove primary status from new owner in ALL organizations (including this one)
            OrganizationMember.objects.filter(
                user=new_owner_membership.user, is_primary=True
            ).update(is_primary=False)

            # Set primary status for new owner in THIS organization
            new_owner_membership.is_primary = True
            new_owner_membership.role = "owner"  # Ensure they have owner role
            new_owner_membership.save()

            # Log the transfer
            from invoicing_app.audit.models import AuditLog

            AuditLog.objects.create(
                entity_type="organization",
                entity_id=org.id,
                action="transfer_ownership",
                actor=request.user,
                notes=f"Transferred ownership of '{org.name}' from {current_owner_membership.user.email} to {new_owner_membership.user.email}",
                ip_address=request.META.get("REMOTE_ADDR"),
            )

        return Response(
            {
                "success": f"Ownership transferred to {new_owner_membership.user.get_full_name() or new_owner_membership.user.username}"
            }
        )


class OrganizationMemberViewSet(viewsets.ModelViewSet):
    """
    API endpoints for organization membership management.
    """

    queryset = OrganizationMember.objects.all()
    serializer_class = OrganizationMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Only return members from organizations the user belongs to"""
        user = self.request.user
        return OrganizationMember.objects.filter(
            organization__members__user=user, is_active=True
        ).distinct()


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    API endpoints for subscription management.
    """

    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Only return subscriptions for organizations the user belongs to"""
        user = self.request.user
        return Subscription.objects.filter(
            organization__members__user=user, is_active=True
        ).distinct()


class InvoiceViewSet(viewsets.ModelViewSet):
    """
    API endpoints for billing invoice management.
    """

    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Only return invoices for organizations the user belongs to"""
        user = self.request.user
        return Invoice.objects.filter(
            organization__members__user=user, is_active=True
        ).distinct()
