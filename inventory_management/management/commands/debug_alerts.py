# inventory_management/management/commands/debug_alerts.py - CREATE THIS FILE
from django.core.management.base import BaseCommand
from datetime import date, timedelta
from inventory_management.models import InventoryItem, Equipment, StockAlert
from multiple_gym.models import Gym


class Command(BaseCommand):
    help = 'Debug why alerts are not being generated'

    def add_arguments(self, parser):
        parser.add_argument('--gym-id', type=int, required=True)

    def handle(self, *args, **options):
        gym_id = options['gym_id']
        
        try:
            gym = Gym.objects.get(id=gym_id)
        except Gym.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Gym {gym_id} not found'))
            return
        
        self.stdout.write(f'🔍 Debugging alerts for gym: {gym.name}')
        
        # 1. Check current alerts
        current_alerts = StockAlert.objects.filter(
            inventory_item__gym=gym,
            is_resolved=False
        ).count() + StockAlert.objects.filter(
            equipment__gym=gym,
            is_resolved=False
        ).count()
        
        self.stdout.write(f'📊 Current unresolved alerts: {current_alerts}')
        
        # 2. Debug inventory items
        self.stdout.write('\n🏪 INVENTORY ANALYSIS:')
        inventory_items = InventoryItem.objects.filter(gym=gym, is_active=True)
        self.stdout.write(f'Total inventory items: {inventory_items.count()}')
        
        if inventory_items.exists():
            for item in inventory_items:
                self.stdout.write(f'\n📦 Item: {item.name}')
                self.stdout.write(f'   Current Stock: {item.current_stock} {item.unit}')
                self.stdout.write(f'   Minimum Stock: {item.minimum_stock} {item.unit}')
                self.stdout.write(f'   Is Low Stock: {item.is_low_stock}')
                self.stdout.write(f'   Auto Reorder: {item.auto_reorder}')
                
                # Check why alert not created
                if item.is_low_stock:
                    self.stdout.write(f'   ⚠️  SHOULD HAVE LOW STOCK ALERT!')
                    
                    # Check if alert exists
                    existing_alert = StockAlert.objects.filter(
                        inventory_item=item,
                        is_resolved=False,
                        alert_type='low_stock'
                    ).first()
                    
                    if existing_alert:
                        self.stdout.write(f'   ✅ Alert exists: {existing_alert.title}')
                    else:
                        self.stdout.write(f'   ❌ NO ALERT FOUND - Creating now...')
                        # Force create alert
                        item.save()  # This should trigger signals
                else:
                    self.stdout.write(f'   ✅ Stock level OK')
        else:
            self.stdout.write('❌ No inventory items found!')
        
        # 3. Debug equipment
        self.stdout.write('\n🏋️ EQUIPMENT ANALYSIS:')
        equipment_items = Equipment.objects.filter(gym=gym, is_active=True)
        self.stdout.write(f'Total equipment: {equipment_items.count()}')
        
        if equipment_items.exists():
            for equipment in equipment_items:
                self.stdout.write(f'\n🔧 Equipment: {equipment.name}')
                self.stdout.write(f'   Next Maintenance: {equipment.next_maintenance_date}')
                self.stdout.write(f'   Warranty End: {equipment.warranty_end_date}')
                self.stdout.write(f'   Needs Maintenance: {equipment.needs_maintenance}')
                
                if equipment.next_maintenance_date:
                    days_until = (equipment.next_maintenance_date - date.today()).days
                    self.stdout.write(f'   Days until maintenance: {days_until}')
                    
                    if days_until <= 7:
                        self.stdout.write(f'   ⚠️  SHOULD HAVE MAINTENANCE ALERT!')
                        # Check if alert exists
                        existing_alert = StockAlert.objects.filter(
                            equipment=equipment,
                            is_resolved=False,
                            alert_type='maintenance_due'
                        ).first()
                        
                        if existing_alert:
                            self.stdout.write(f'   ✅ Alert exists: {existing_alert.title}')
                        else:
                            self.stdout.write(f'   ❌ NO ALERT FOUND - Creating now...')
                            # Force create alert
                            equipment.save()  # This should trigger signals
                    else:
                        self.stdout.write(f'   ✅ Maintenance not due yet')
                
                if equipment.warranty_end_date:
                    days_remaining = (equipment.warranty_end_date - date.today()).days
                    self.stdout.write(f'   Warranty days remaining: {days_remaining}')
                    
                    if 0 <= days_remaining <= 30:
                        self.stdout.write(f'   ⚠️  SHOULD HAVE WARRANTY ALERT!')
                        existing_alert = StockAlert.objects.filter(
                            equipment=equipment,
                            is_resolved=False,
                            alert_type='warranty_expiring'
                        ).first()
                        
                        if existing_alert:
                            self.stdout.write(f'   ✅ Alert exists: {existing_alert.title}')
                        else:
                            self.stdout.write(f'   ❌ NO ALERT FOUND - Creating now...')
                            equipment.save()  # Force trigger
                    else:
                        self.stdout.write(f'   ✅ Warranty not expiring soon')
        else:
            self.stdout.write('❌ No equipment found!')
        
        # 4. Final alert count
        final_alerts = StockAlert.objects.filter(
            inventory_item__gym=gym,
            is_resolved=False
        ).count() + StockAlert.objects.filter(
            equipment__gym=gym,
            is_resolved=False
        ).count()
        
        self.stdout.write(f'\n📊 Final alert count: {final_alerts}')
        
        if final_alerts > 0:
            self.stdout.write('✅ Alerts found! Check your alerts page.')
        else:
            self.stdout.write('❌ No alerts generated. Your data might not meet alert conditions.')
            self.stdout.write('\n💡 SUGGESTIONS:')
            self.stdout.write('1. Set some inventory items current_stock <= minimum_stock')
            self.stdout.write('2. Set equipment next_maintenance_date within 7 days')
            self.stdout.write('3. Set equipment warranty_end_date within 30 days')