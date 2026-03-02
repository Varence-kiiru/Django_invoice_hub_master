from rest_framework import viewsets, permissions
from invoicing_app.user_management.models import UserRole, CustomUser
from invoicing_app.core.permissions import IsAdmin, CanManageUsers
from .serializers import UserRoleSerializer, CustomUserSerializer


class UserRoleViewSet(viewsets.ModelViewSet):
    """User role management - admin only."""
    queryset = UserRole.objects.all().order_by('name')
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']


class CustomUserViewSet(viewsets.ModelViewSet):
    """Custom user profile management with role-based access control."""
    queryset = CustomUser.objects.all().order_by('user__email')
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageUsers]
    filterset_fields = ['role', 'is_active']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'phone']
    
    def get_queryset(self):
        """Filter users based on role."""
        user = self.request.user
        try:
            profile = user.invoicing_profile
            # Admins see all users
            if profile.role == 'admin':
                return CustomUser.objects.all().order_by('user__email')
            # Regular users can only see their own profile
            return CustomUser.objects.filter(user=user)
        except:
            pass
        return CustomUser.objects.none()
