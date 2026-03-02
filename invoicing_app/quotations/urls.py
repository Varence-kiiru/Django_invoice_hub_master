"""
URL routing for quote management views.
"""
from django.urls import path
from . import views_html

app_name = 'quotations'

urlpatterns = [
    # ━━━ Quote CRUD ━━━
    path('', views_html.quotes_list_view, name='list'),
    path('create/', views_html.quote_create_view, name='create'),
    path('<int:pk>/', views_html.quote_detail_view, name='detail'),
    path('<int:pk>/edit/', views_html.quote_edit_view, name='edit'),
    path('<int:pk>/delete/', views_html.quote_delete_view, name='delete'),

    # ━━━ Line Items ━━━
    path('<int:pk>/add-item/', views_html.add_quote_line_item_view, name='add-item'),
    path('<int:pk>/item/<int:item_id>/edit/', views_html.edit_quote_line_item_view, name='edit-item'),
    path('<int:pk>/item/<int:item_id>/delete/', views_html.delete_quote_line_item_view, name='delete-item'),

    # ━━━ Quote Management ━━━
    path('<int:pk>/issue/', views_html.quote_issue_confirm_view, name='issue'),
    path('<int:pk>/convert/', views_html.quote_convert_view, name='convert'),
    path('<int:pk>/accept/', views_html.quote_accept_view, name='accept'),
    path('<int:pk>/send/', views_html.quote_send_view, name='send'),
    path('<int:pk>/pdf/', views_html.quote_pdf_view, name='pdf'),
    path('<int:pk>/print/', views_html.quote_print_view, name='print'),
    path('<int:pk>/download/', views_html.quote_download_view, name='download'),
]

