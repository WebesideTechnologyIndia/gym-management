from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from .models import InventoryItem, Equipment, StockTransaction, StockAlert, MaintenanceRecord


@receiver(post_save, sender=InventoryItem)
def generate_inventory_alerts(sender, instance, created, **kwargs):
    """Automatically generate alerts when inventory items are saved"""
    print(f"🔍 Auto-checking alerts for: {instance.name}")
    
    try:
        # Clear existing alerts for this item to avoid duplicates
        StockAlert.objects.filter(
            inventory_item=instance,
            is_resolved=False,
            alert_type__in=['low_stock', 'reorder_needed']
        ).delete()
        
        # Convert float constants to Decimal for proper arithmetic
        HALF = Decimal('0.5')
        ZERO = Decimal('0')
        
        # Ensure current_stock and minimum_stock are Decimals
        current_stock = Decimal(str(instance.current_stock)) if instance.current_stock else ZERO
        minimum_stock = Decimal(str(instance.minimum_stock)) if instance.minimum_stock else ZERO
        
        # 1. LOW STOCK ALERT
        if instance.is_low_stock:
            # Determine priority based on how critical the stock level is
            if current_stock == ZERO:
                priority = 'critical'
                title = f'OUT OF STOCK: {instance.name}'
                message = f'{instance.name} is completely out of stock! Immediate restocking required.'
            elif current_stock <= (minimum_stock * HALF):  # 50% below minimum - FIXED!
                priority = 'critical' 
                title = f'CRITICALLY LOW: {instance.name}'
                message = f'{instance.name} is critically low. Current: {current_stock} {instance.unit}, Minimum: {minimum_stock} {instance.unit}.'
            else:
                priority = 'high'
                title = f'Low Stock: {instance.name}'
                message = f'{instance.name} is below minimum stock level. Current: {current_stock} {instance.unit}, Minimum: {minimum_stock} {instance.unit}.'
            
            alert = StockAlert.objects.create(
                alert_type='low_stock',
                priority=priority,
                inventory_item=instance,
                title=title,
                message=message
            )
            print(f"✅ Created LOW STOCK alert: {alert.title}")
        
        # 2. REORDER ALERT (if auto_reorder is enabled)
        if instance.auto_reorder and instance.is_low_stock:
            StockAlert.objects.create(
                alert_type='reorder_needed',
                priority='medium',
                inventory_item=instance,
                title=f'Reorder Required: {instance.name}',
                message=f'{instance.name} needs restocking. Suggested reorder quantity: {instance.reorder_quantity} {instance.unit}. Contact vendor: {instance.primary_vendor.name if instance.primary_vendor else "Not specified"}.'
            )
            print(f"✅ Created REORDER alert for: {instance.name}")
    
    except Exception as e:
        print(f"❌ Error in generate_inventory_alerts: {str(e)}")
        # Don't re-raise to avoid breaking the transaction


@receiver(post_save, sender=Equipment)
def generate_equipment_alerts(sender, instance, created, **kwargs):
    """Automatically generate alerts for equipment"""
    print(f"🔍 Auto-checking equipment alerts for: {instance.name}")
    
    try:
        # Clear existing alerts for this equipment
        StockAlert.objects.filter(
            equipment=instance,
            is_resolved=False,
            alert_type__in=['maintenance_due', 'warranty_expiring']
        ).delete()
        
        # 1. MAINTENANCE DUE ALERT
        if instance.next_maintenance_date:
            days_until_maintenance = (instance.next_maintenance_date - date.today()).days
            
            # Create alert if maintenance is due within 7 days or overdue
            if days_until_maintenance <= 7:
                if days_until_maintenance < 0:  # Overdue
                    priority = 'critical'
                    title = f'MAINTENANCE OVERDUE: {instance.name}'
                    message = f'{instance.name} maintenance is {abs(days_until_maintenance)} days overdue! Immediate attention required.'
                elif days_until_maintenance == 0:  # Due today
                    priority = 'critical'
                    title = f'MAINTENANCE DUE TODAY: {instance.name}'
                    message = f'{instance.name} maintenance is due today. Please schedule immediately.'
                else:  # Due within 7 days
                    priority = 'high' if days_until_maintenance <= 3 else 'medium'
                    title = f'Maintenance Due Soon: {instance.name}'
                    message = f'{instance.name} maintenance is due in {days_until_maintenance} day(s) on {instance.next_maintenance_date}.'
                
                alert = StockAlert.objects.create(
                    alert_type='maintenance_due',
                    priority=priority,
                    equipment=instance,
                    title=title,
                    message=message
                )
                print(f"✅ Created MAINTENANCE alert: {alert.title}")
        
        # 2. WARRANTY EXPIRING ALERT
        if instance.warranty_end_date:
            days_remaining = (instance.warranty_end_date - date.today()).days
            
            # Create alert if warranty expires within 30 days
            if 0 <= days_remaining <= 30:
                if days_remaining <= 7:
                    priority = 'critical'
                    title = f'WARRANTY EXPIRING SOON: {instance.name}'
                elif days_remaining <= 15:
                    priority = 'high'
                    title = f'Warranty Expiring: {instance.name}'
                else:
                    priority = 'medium'
                    title = f'Warranty Alert: {instance.name}'
                
                message = f'Warranty for {instance.name} expires in {days_remaining} day(s) on {instance.warranty_end_date}. Consider renewal or replacement.'
                
                alert = StockAlert.objects.create(
                    alert_type='warranty_expiring',
                    priority=priority,
                    equipment=instance,
                    title=title,
                    message=message
                )
                print(f"✅ Created WARRANTY alert: {alert.title}")
    
    except Exception as e:
        print(f"❌ Error in generate_equipment_alerts: {str(e)}")
        # Don't re-raise to avoid breaking the transaction


@receiver(post_save, sender=StockTransaction)
def handle_stock_transaction_alerts(sender, instance, created, **kwargs):
    """Generate alerts when stock transactions occur"""
    try:
        if created:  # Only for new transactions
            print(f"🔍 Transaction created for: {instance.item.name}")
            
            # Refresh the item from database first
            instance.item.refresh_from_db()
            
            # Manually trigger the alert check instead of calling save()
            # This avoids the recursive save issue
            generate_inventory_alerts(sender=InventoryItem, instance=instance.item, created=False)
    
    except Exception as e:
        print(f"❌ Error in handle_stock_transaction_alerts: {str(e)}")
        # Don't re-raise to avoid breaking the transaction


@receiver(post_save, sender=MaintenanceRecord)
def handle_maintenance_completion(sender, instance, created, **kwargs):
    """Handle maintenance record updates"""
    try:
        if instance.status == 'completed':
            # Resolve maintenance alerts for this equipment
            resolved_count = StockAlert.objects.filter(
                equipment=instance.equipment,
                alert_type='maintenance_due',
                is_resolved=False
            ).update(
                is_resolved=True,
                resolved_at=timezone.now(),
                resolved_by=instance.created_by
            )
            
            if resolved_count > 0:
                print(f"✅ Auto-resolved {resolved_count} maintenance alerts for {instance.equipment.name}")
    
    except Exception as e:
        print(f"❌ Error in handle_maintenance_completion: {str(e)}")
        # Don't re-raise to avoid breaking the transaction