from django.urls import path 
from . import views
from django.http import request




urlpatterns=[
    path('', views.home, name='dashboard-home'),
    path('delete/<int:alert_id>/', views.delete_alert, name='delete-alert'),
    path('stock-groups/', views.stock_group_list, name='stock-group-list'),
    path('stock-groups/create/', views.stock_group_create, name='stock-group-create'),
    path('stock-groups/<int:group_id>/update/', views.stock_group_update, name='stock-group-update'),
    path('stock-groups/<int:group_id>/delete/', views.stock_group_delete, name='stock-group-delete'),
    ]