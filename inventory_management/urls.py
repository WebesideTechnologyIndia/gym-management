# inventory_management/urls.py - FIXED VERSION

from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('dashboard/<int:gym_id>/', views.inventory_dashboard, name='dashboard'),
    
    # Equipment URLs - EDIT/DELETE ADDED
    path('equipment/<int:gym_id>/', views.equipment_list, name='equipment_list'),
    path('equipment/<int:gym_id>/add/', views.add_equipment, name='add_equipment'),
    path('equipment/<int:gym_id>/<int:equipment_id>/edit/', views.add_equipment, name='edit_equipment'),
    path('equipment/<int:gym_id>/<int:equipment_id>/delete/', views.delete_equipment, name='delete_equipment'),
    path('equipment/<int:gym_id>/<int:equipment_id>/', views.equipment_detail, name='equipment_detail'),
    
    # Equipment Category URLs - FIXED WITH GYM_ID
    path('categories/<int:gym_id>/', views.equipment_category_list, name='equipment_category_list'),
    path('categories/<int:gym_id>/add/', views.add_equipment_category, name='add_equipment_category'),
    path('categories/<int:gym_id>/<int:category_id>/edit/', views.edit_equipment_category, name='edit_equipment_category'),
    path('categories/<int:gym_id>/<int:category_id>/delete/', views.delete_equipment_category, name='delete_equipment_category'),
    
    # Maintenance URLs
    path('maintenance/<int:gym_id>/', views.maintenance_list, name='maintenance_list'),
    path('maintenance/<int:gym_id>/schedule/', views.schedule_maintenance, name='schedule_maintenance'),
    path('maintenance/<int:gym_id>/schedule/<int:equipment_id>/', views.schedule_maintenance, name='schedule_equipment_maintenance'),
    path('maintenance/<int:gym_id>/<int:maintenance_id>/update/', views.update_maintenance, name='update_maintenance'),
    
    # Inventory URLs
    path('inventory/<int:gym_id>/', views.inventory_list, name='inventory_list'),
    path('inventory/<int:gym_id>/add/', views.add_inventory_item, name='add_inventory_item'),
    path('inventory/<int:gym_id>/<int:item_id>/', views.inventory_detail, name='inventory_detail'),
    path('inventory/<int:gym_id>/<int:item_id>/transaction/', views.stock_transaction, name='stock_transaction'),
    
    # Vendor URLs - FIXED और COMPLETE
    path('gym/<int:gym_id>/vendors/', views.vendor_list, name='vendor_list'),
    path('gym/<int:gym_id>/vendors/create/', views.add_vendor, name='vendor_create'),
    path('gym/<int:gym_id>/vendors/<int:vendor_id>/', views.vendor_detail, name='vendor_detail'),
    path('gym/<int:gym_id>/vendors/<int:vendor_id>/edit/', views.vendor_edit, name='vendor_edit'),
    path('gym/<int:gym_id>/vendors/<int:vendor_id>/delete/', views.vendor_delete, name='vendor_delete'),
    
    # Reports URLs
    path('reports/<int:gym_id>/equipment/', views.equipment_reports, name='equipment_reports'),
    path('reports/<int:gym_id>/inventory/', views.inventory_reports, name='inventory_reports'),
    
    # Alerts URLs
    path('alerts/<int:gym_id>/', views.alerts_view, name='alerts_view'),
    path('alerts/<int:gym_id>/<int:alert_id>/resolve/', views.resolve_alert, name='resolve_alert'),
    path('alerts/<int:gym_id>/<int:alert_id>/read/', views.mark_alert_as_read, name='mark_alert_as_read'),
    path('alerts/<int:gym_id>/mark-all-read/', views.mark_all_alerts_as_read, name='mark_all_alerts_as_read'),
    path('alerts/<int:gym_id>/resolve-all/', views.resolve_all_alerts, name='resolve_all_alerts'),
    
    # AJAX URLs
    path('ajax/equipment/<int:equipment_id>/data/', views.get_equipment_maintenance_data, name='equipment_data'),
    path('ajax/inventory/<int:item_id>/data/', views.get_inventory_item_data, name='inventory_data'),

    # Inventory Category URLs - FIXED WITH GYM_ID
    path('inventory-categories/<int:gym_id>/', views.inventory_category_list, name='inventory_category_list'),
    path('inventory-categories/<int:gym_id>/add/', views.add_inventory_category, name='add_inventory_category'),
    path('inventory-categories/<int:gym_id>/<int:category_id>/edit/', views.edit_inventory_category, name='edit_inventory_category'),
    path('inventory-categories/<int:gym_id>/<int:category_id>/delete/', views.delete_inventory_category, name='delete_inventory_category'),
]