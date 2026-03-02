from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from .models import UserRole, CustomUser
from invoicing_app.core.permissions import ALL_PERMISSIONS, get_all_permission_groups


class PermissionsWidget(admin.ModelAdmin):
    """Custom widget for editing permissions."""
    pass


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'permission_count', 'is_active', 'created_at', 'edit_permissions_link')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'permissions_display', 'edit_permissions_link')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Permissions', {
            'fields': ('permissions_display', 'permissions'),
            'description': 'Select which permissions this role should have. Use the checkbox table below to customize.'
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    formfield_overrides = {
        models.JSONField: {'widget': admin.widgets.AdminTextareaWidget},
    }
    
    def permission_count(self, obj):
        """Display the number of permissions assigned to this role."""
        count = len(obj.permissions) if obj.permissions else 0
        return format_html(
            '<span style="background-color: #e8f4f8; padding: 3px 8px; border-radius: 3px;">{} permissions</span>',
            count
        )
    permission_count.short_description = 'Permissions'
    
    def permissions_display(self, obj):
        """Display permissions in a readable format with category grouping."""
        if not obj.permissions:
            return '<p style="color: #999;">No permissions assigned</p>'
        
        permissions = obj.permissions or []
        groups = get_all_permission_groups()
        
        html = '<div style="max-height: 400px; overflow-y: auto;">'
        
        for group_name, group_perms in sorted(groups.items()):
            assigned = [p for p in group_perms.keys() if p in permissions]
            if assigned:
                html += f'<div style="margin-bottom: 15px;">'
                html += f'<strong style="color: #333; text-transform: capitalize;">{group_name}</strong> ({len(assigned)}/{len(group_perms)})'
                html += '<ul style="margin: 5px 0 0 20px; padding: 0;">'
                for perm in assigned:
                    desc = group_perms[perm].get('description', perm) if isinstance(group_perms[perm], dict) else group_perms[perm]
                    html += f'<li style="margin: 2px 0; font-size: 12px;">✓ {perm}</li>'
                html += '</ul></div>'
        
        html += '</div>'
        return format_html(html)
    permissions_display.short_description = 'Assigned Permissions'
    
    def edit_permissions_link(self, obj):
        """Provide a link to the permission editor."""
        if obj.id:
            from django.urls import reverse
            url = reverse('admin:user_management_userrole_change', args=[obj.id])
            return format_html(
                '<a class="button" href="{}#id_permissions" style="background-color: #417690;">Edit Permissions</a>',
                url
            )
        return '-'
    edit_permissions_link.short_description = 'Actions'
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize the form to show permission checkboxes."""
        form = super().get_form(request, obj, **kwargs)
        
        # Store ALL_PERMISSIONS in form for context
        form.ALL_PERMISSIONS = ALL_PERMISSIONS
        form.PERMISSION_GROUPS = get_all_permission_groups()
        
        return form


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    fieldsets = (
        ('User Link', {
            'fields': ('user', 'uuid')
        }),
        ('Profile', {
            'fields': ('phone', 'role')
        }),
        ('Audit', {
            'fields': ('is_active', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
