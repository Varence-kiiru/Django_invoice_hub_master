"""URL routing for product management views."""
from django.urls import path
from . import views_html

app_name = 'products'

urlpatterns = [
    # ━━━ Product CRUD ━━━
    path('', views_html.products_list_view, name='list'),
    path('create/', views_html.products_create_view, name='create'),
    path('<int:pk>/', views_html.products_detail_view, name='detail'),
    path('<int:pk>/edit/', views_html.products_edit_view, name='edit'),
    path('<int:pk>/delete/', views_html.products_delete_view, name='delete'),
    
    # ━━━ Product Management ━━━
    path('import/', views_html.products_import_view, name='import'),
    path('export/', views_html.products_export_view, name='export'),
    path('bulk-delete/', views_html.products_bulk_delete_view, name='bulk-delete'),
    path('<int:pk>/toggle-status/', views_html.products_toggle_status_view, name='toggle-status'),
    
    # ━━━ Category Management ━━━
    path('categories/', views_html.product_categories_view, name='categories'),
    path('categories/create/', views_html.category_create_view, name='category-create'),
    path('categories/<int:pk>/edit/', views_html.category_edit_view, name='category-edit'),
    path('categories/<int:pk>/delete/', views_html.category_delete_view, name='category-delete'),
]
