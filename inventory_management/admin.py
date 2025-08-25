from django.contrib import admin

# Register your models here.
# inventory_management/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from datetime import date
from .models import (
    EquipmentCategory, Vendor, Equipment, MaintenanceRecord,
    InventoryCategory, InventoryItem, StockTransaction, StockAlert
)

@admin.register(EquipmentCategory)
class EquipmentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'icon', 'equipment_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    def equipment_count(self, obj):
        return obj.equipment.count()
    equipment_count.short_description = 'Equipment Count'

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'contact_person', 'phone', 'city', 'state', 
        'rating_display', 'is_active', 'created_at'
    ]
    list_filter = ['rating', 'is_active', 'state', 'city', 'created_at']
    search_fields = ['name', 'contact_person', 'phone', 'email', 'gst_number', 'pan_number']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'contact_person', 'email', 'phone', 'alternate_phone')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'pincode')
        }),
        ('Business Details', {
            'fields': ('gst_number', 'pan_number')
        }),
        ('Rating & Status', {
            'fields': ('rating', 'is_active', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def rating_display(self, obj):
        stars = '⭐' * obj.rating
        return format_html(f'<span title="{obj.rating}/5">{stars}</span>')
    rating_display.short_description = 'Rating'

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'serial_number', 'category', 'brand', 'gym', 
        'status_display', 'condition_display', 'warranty_status',
        'maintenance_status', 'purchase_date'
    ]
    list_filter = [
        'status', 'condition', 'category', 'vendor', 'gym',
        'purchase_date', 'is_active'
    ]
    search_fields = [
        'name', 'brand', 'model_number', 'serial_number', 
        'location', 'invoice_number'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'current_value', 'warranty_days_remaining', 'maintenance_overdue_days',
        'created_at', 'updated_at'
    ]
    date_hierarchy = 'purchase_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'brand', 'model_number', 'serial_number', 'gym')
        }),
        ('Purchase Information', {
            'fields': ('vendor', 'purchase_date', 'purchase_price', 'invoice_number')
        }),
        ('Warranty Information', {
            'fields': (
                'warranty_period_months', 'warranty_start_date', 'warranty_end_date',
                'warranty_days_remaining'
            )
        }),
        ('Current Status', {
            'fields': ('status', 'condition', 'location')
        }),
        ('Maintenance', {
            'fields': (
                'last_maintenance_date', 'next_maintenance_date', 
                'maintenance_frequency_days', 'maintenance_overdue_days'
            )
        }),
        ('Financial', {
            'fields': ('depreciation_rate', 'current_value')
        }),
        ('Additional Information', {
            'fields': ('specifications', 'notes', 'image')
        }),
        ('System Information', {
            'fields': ('is_active', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def status_display(self, obj):
        colors = {
            'working': 'green',
            'maintenance': 'orange',
            'repair': 'red',
            'out_of_order': 'darkred',
            'disposed': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            f'<span style="color: {color}; font-weight: bold;">{obj.get_status_display()}</span>'
        )
    status_display.short_description = 'Status'
    
    def condition_display(self, obj):
        colors = {
            'excellent': 'green',
            'good': 'lightgreen',
            'fair': 'orange',
            'poor': 'red',
            'critical': 'darkred'
        }
        color = colors.get(obj.condition, 'black')
        return format_html(
            f'<span style="color: {color}; font-weight: bold;">{obj.get_condition_display()}</span>'
        )
    condition_display.short_description = 'Condition'
    
    def warranty_status(self, obj):
        if obj.is_warranty_valid:
            days_left = obj.warranty_days_remaining
            if days_left <= 30:
                return format_html(
                    f'<span style="color: orange;">⚠️ {days_left} days left</span>'
                )
            return format_html(
                f'<span style="color: green;">✅ Valid ({days_left} days)</span>'
            )
        return format_html('<span style="color: red;">❌ Expired</span>')
    warranty_status.short_description = 'Warranty'
    
    def maintenance_status(self, obj):
        if obj.needs_maintenance:
            overdue_days = obj.maintenance_overdue_days
            if overdue_days > 0:
                return format_html(
                    f'<span style="color: red;">🔧 Overdue ({overdue_days} days)</span>'
                )
            return format_html('<span style="color: orange;">🔧 Due</span>')
        return format_html('<span style="color: green;">✅ Current</span>')
    maintenance_status.short_description = 'Maintenance'

@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = [
        'equipment', 'maintenance_type', 'scheduled_date', 'actual_date',
        'status_display', 'total_cost', 'technician_name', 'vendor'
    ]
    list_filter = [
        'maintenance_type', 'status', 'scheduled_date', 'actual_date',
        'vendor', 'equipment__category'
    ]
    search_fields = [
        'equipment__name', 'equipment__serial_number', 'technician_name',
        'description', 'work_performed'
    ]
    ordering = ['-scheduled_date']
    readonly_fields = ['total_cost', 'created_at', 'updated_at']
    date_hierarchy = 'scheduled_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('equipment', 'maintenance_type', 'description')
        }),
        ('Scheduling', {
            'fields': ('scheduled_date', 'actual_date', 'status')
        }),
        ('Work Details', {
            'fields': ('work_performed', 'parts_replaced', 'downtime_hours')
        }),
        ('Personnel', {
            'fields': ('technician_name', 'vendor')
        }),
        ('Costs', {
            'fields': ('labor_cost', 'parts_cost', 'total_cost')
        }),
        ('Follow-up', {
            'fields': ('next_maintenance_due', 'notes')
        }),
        ('Images', {
            'fields': ('before_images', 'after_images'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def status_display(self, obj):
        colors = {
            'scheduled': 'blue',
            'in_progress': 'orange',
            'completed': 'green',
            'cancelled': 'red'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            f'<span style="color: {color}; font-weight: bold;">{obj.get_status_display()}</span>'
        )
    status_display.short_description = 'Status'

@admin.register(InventoryCategory)
class InventoryCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'icon', 'items_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Items Count'

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'current_stock', 'unit', 'stock_status',
        'cost_price', 'selling_price', 'total_value', 'primary_vendor'
    ]
    list_filter = [
        'category', 'unit', 'auto_reorder', 'has_expiry', 'is_active',
        'primary_vendor', 'gym'
    ]
    search_fields = ['name', 'brand', 'sku', 'barcode', 'description']
    ordering = ['name']
    readonly_fields = ['total_value', 'stock_percentage', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'brand', 'description', 'gym')
        }),
        ('Stock Information', {
            'fields': (
                'current_stock', 'minimum_stock', 'maximum_stock', 'unit',
                'stock_percentage'
            )
        }),
        ('Pricing', {
            'fields': ('cost_price', 'selling_price', 'total_value')
        }),
        ('Auto Reorder', {
            'fields': ('auto_reorder', 'reorder_quantity')
        }),
        ('Vendor & Location', {
            'fields': ('primary_vendor', 'location')
        }),
        ('Product Codes', {
            'fields': ('sku', 'barcode')
        }),
        ('Expiry Management', {
            'fields': ('has_expiry', 'expiry_alert_days'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('is_active', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def stock_status(self, obj):
        if obj.is_low_stock:
            return format_html('<span style="color: red;">🔴 Low Stock</span>')
        elif obj.current_stock == 0:
            return format_html('<span style="color: darkred;">❌ Out of Stock</span>')
        else:
            return format_html('<span style="color: green;">✅ In Stock</span>')
    stock_status.short_description = 'Stock Status'

@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'item', 'transaction_type_display', 'quantity', 'unit_price',
        'total_amount', 'stock_before', 'stock_after', 'transaction_date', 'vendor'
    ]
    list_filter = [
        'transaction_type', 'transaction_date', 'vendor', 'item__category',
        'expiry_date'
    ]
    search_fields = [
        'item__name', 'reference_number', 'batch_number', 'notes'
    ]
    ordering = ['-transaction_date']
    readonly_fields = ['total_amount', 'stock_after']
    date_hierarchy = 'transaction_date'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('item', 'transaction_type', 'quantity', 'unit_price', 'total_amount')
        }),
        ('Stock Levels', {
            'fields': ('stock_before', 'stock_after')
        }),
        ('Reference Information', {
            'fields': ('reference_number', 'vendor', 'transaction_date')
        }),
        ('Batch & Expiry', {
            'fields': ('batch_number', 'expiry_date'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_by')
        })
    )
    
    def transaction_type_display(self, obj):
        colors = {
            'purchase': 'green',
            'sale': 'blue',
            'adjustment': 'orange',
            'damage': 'red',
            'return': 'purple',
            'transfer': 'brown',
            'expired': 'gray'
        }
        color = colors.get(obj.transaction_type, 'black')
        return format_html(
            f'<span style="color: {color}; font-weight: bold;">{obj.get_transaction_type_display()}</span>'
        )
    transaction_type_display.short_description = 'Type'

@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = [
        'alert_type_display', 'title', 'priority_display', 'equipment', 
        'inventory_item', 'is_read', 'is_resolved', 'created_at'
    ]
    list_filter = [
        'alert_type', 'priority', 'is_read', 'is_resolved', 'created_at'
    ]
    search_fields = ['title', 'message']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('alert_type', 'priority', 'title', 'message')
        }),
        ('Related Objects', {
            'fields': ('equipment', 'inventory_item')
        }),
        ('Status', {
            'fields': ('is_read', 'is_resolved', 'resolved_by', 'resolved_at')
        }),
        ('System Information', {
            'fields': ('created_at',)
        })
    )
    
    def alert_type_display(self, obj):
        colors = {
            'low_stock': 'orange',
            'expiry_soon': 'yellow',
            'expired': 'red',
            'maintenance_due': 'blue',
            'warranty_expiring': 'purple',
            'reorder_needed': 'brown'
        }
        color = colors.get(obj.alert_type, 'black')
        return format_html(
            f'<span style="color: {color}; font-weight: bold;">{obj.get_alert_type_display()}</span>'
        )
    alert_type_display.short_description = 'Alert Type'
    
    def priority_display(self, obj):
        colors = {
            'low': 'green',
            'medium': 'orange',
            'high': 'red',
            'critical': 'darkred'
        }
        color = colors.get(obj.priority, 'black')
        return format_html(
            f'<span style="color: {color}; font-weight: bold; text-transform: uppercase;">{obj.priority}</span>'
        )
    priority_display.short_description = 'Priority'
    
    actions = ['mark_as_read', 'mark_as_resolved']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} alerts marked as read.')
    mark_as_read.short_description = 'Mark selected alerts as read'
    
    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            is_resolved=True,
            resolved_by=request.user,
            resolved_at=timezone.now()
        )
        self.message_user(request, f'{updated} alerts marked as resolved.')
    mark_as_resolved.short_description = 'Mark selected alerts as resolved'

# Custom admin site configuration
admin.site.site_header = "Gym Inventory Management"
admin.site.site_title = "Gym Admin"
admin.site.index_title = "Inventory Management System"