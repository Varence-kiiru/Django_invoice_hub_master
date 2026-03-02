"""URL routing for client management views."""
from django.urls import path
from . import views_html, views

app_name = 'clients'

urlpatterns = [
    # ━━━ Client CRUD ━━━
    path('', views_html.clients_list_view, name='list'),
    path('create/', views_html.clients_create_view, name='create'),
    path('<int:pk>/', views_html.clients_detail_view, name='detail'),
    path('<int:pk>/edit/', views.client_edit, name='edit'),
    path('<int:pk>/delete/', views_html.clients_delete_view, name='delete'),
    
    # ━━━ Client Management ━━━
    path('<int:pk>/addresses/', views_html.client_addresses_view, name='addresses'),
    path('<int:pk>/contacts/', views_html.client_contacts_view, name='contacts'),
    path('<int:pk>/statement/', views_html.client_statements_view, name='statement'),
    
    # ━━━ Address/Contact Deletion ━━━
    path('addresses/<int:pk>/delete/', views_html.address_delete_view, name='address-delete'),
    path('contacts/<int:pk>/delete/', views_html.contact_delete_view, name='contact-delete'),
]
