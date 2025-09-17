# Quick Fix Command - inventory_management/management/commands/force_alerts.py
from django.core.management.base import BaseCommand
from datetime import date, timedelta
from decimal import Decimal
from inventory_management.models import InventoryItem, Equipment


class Command(BaseCommand):
    help = 'Force create some alerts by modifying existing data temporarily'

    def add_arguments(self, parser):
        parser.add_argument('--gym-id', type=int, required=True)

    def handle(self, *args, **options):
        gym_id = options['gym_id']
        
        # 1. Force low stock on first inventory item
        item = InventoryItem.objects.filter(gym_id=gym_id, is_active=True).first()
        if item:
            old_stock = item.current_stock
            old_min = item.minimum_stock
            
            # Temporarily make it low stock
            item.current_stock = Decimal('1')
            item.minimum_stock = Decimal('10') 
            item.auto_reorder = True
            item.reorder_quantity = Decimal('20')
            item.save()  # This should create alerts
            
            self.stdout.write(f'✅ Modified {item.name}: Stock {old_stock}→{item.current_stock}, Min {old_min}→{item.minimum_stock}')
        
        # 2. Force maintenance due on first equipment
        equipment = Equipment.objects.filter(gym_id=gym_id, is_active=True).first()
        if equipment:
            old_date = equipment.next_maintenance_date
            old_warranty = equipment.warranty_end_date
            
            # Make maintenance due tomorrow and warranty expiring in 15 days
            equipment.next_maintenance_date = date.today() + timedelta(days=1)
            equipment.warranty_end_date = date.today() + timedelta(days=15)
            equipment.save()  # This should create alerts
            
            self.stdout.write(f'✅ Modified {equipment.name}: Maintenance {old_date}→{equipment.next_maintenance_date}')
            self.stdout.write(f'   Warranty {old_warranty}→{equipment.warranty_end_date}')
        
        self.stdout.write('\n🎯 Check your alerts page now - you should see alerts!')
        self.stdout.write(f'🌐 Visit: /inventory/alerts/{gym_id}/')