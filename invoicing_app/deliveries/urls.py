"""URL configuration for deliveries app."""
from django.urls import path
from invoicing_app.deliveries import views

app_name = 'deliveries'

urlpatterns = [
    # ━━━ Delivery Management ━━━
    path('', views.deliveries_list_view, name='list'),
    path('<int:pk>/', views.delivery_detail_view, name='detail'),
    path('create/', views.delivery_create_view, name='create'),
    path('create/<int:invoice_id>/', views.delivery_create_view, name='create_from_invoice'),
    path('<int:pk>/edit/', views.delivery_edit_view, name='edit'),
    path('<int:pk>/delete/', views.delivery_delete_view, name='delete'),
    
    # ━━━ PDF & Print ━━━
    path('<int:pk>/pdf/', views.delivery_pdf_view, name='pdf'),
    
    # ━━━ API Endpoints ━━━
    path('api/invoice/<int:invoice_id>/details/', views.invoice_details_api, name='invoice_details_api'),
]
