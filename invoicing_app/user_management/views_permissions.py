"""
Permission management views - CONSOLIDATED INTO CORE APP

This module previously contained permission management views and APIs.
All functionality has been consolidated into:

📍 LOCATION: invoicing_app/core/views_html.py
   - API Endpoints: get_permissions_api(), get_role_permissions_api(), update_role_permissions_api()
   - Routing: invoicing_app/core/urls.py

📍 API ENDPOINTS (New Location):
   GET  /api/system/permissions/
   GET  /api/system/roles/<id>/permissions/
   POST /api/system/roles/<id>/update-permissions/

📍 WEB INTERFACE (Existing URLs):
   GET  /system/roles/           - Roles management
   GET  /system/users/           - User management
   GET  /system/users/create-edit/ - Create/edit users
   POST /system/users/create-edit/ - Save users

MIGRATION NOTES:
- Old URLs (/users/admin/*) removed to avoid duplication
- All API endpoints now under /api/system/ for consistency
- Integrated with existing system admin interface
- Django system checks: PASSING ✓

This file kept as documentation. Can be safely deleted.
"""

