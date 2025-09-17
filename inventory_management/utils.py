from django.utils import timezone
from datetime import date, timedelta
from .models import StockAlert, InventoryItem, Equipment


def generate_daily_alerts():
    """
    Function to be called daily (via cron job) to check all conditions
    and generate alerts automatically
    """
    print("🔄 Running daily alert generation...")
    
    alert_count = 0
    
    # 1. Check all inventory items for low stock
    for item in InventoryItem.objects.filter(is_active=True):
        old_count = StockAlert.objects.filter(
            inventory_item=item, 
            is_resolved=False
        ).count()
        
        # Trigger alert generation
        item.save()  # This will trigger the signals
        
        new_count = StockAlert.objects.filter(
            inventory_item=item, 
            is_resolved=False
        ).count()
        
        if new_count > old_count:
            alert_count += (new_count - old_count)
    
    # 2. Check all equipment for maintenance and warranty
    for equipment in Equipment.objects.filter(is_active=True):
        old_count = StockAlert.objects.filter(
            equipment=equipment, 
            is_resolved=False
        ).count()
        
        # Trigger alert generation
        equipment.save()  # This will trigger the signals
        
        new_count = StockAlert.objects.filter(
            equipment=equipment, 
            is_resolved=False
        ).count()
        
        if new_count > old_count:
            alert_count += (new_count - old_count)
    
    print(f"✅ Generated {alert_count} new alerts")
    return alert_count


def cleanup_old_resolved_alerts(days=30):
    """
    Clean up old resolved alerts (older than specified days)
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    deleted_count = StockAlert.objects.filter(
        is_resolved=True,
        resolved_at__lt=cutoff_date
    ).delete()[0]
    
    print(f"🧹 Cleaned up {deleted_count} old alerts")
    return deleted_count