from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from inventory_management.models import InventoryItem, Equipment


class Command(BaseCommand):
    help = 'Check and generate alerts for all items and equipment'

    def add_arguments(self, parser):
        parser.add_argument('--gym-id', type=int, help='Check alerts for specific gym only')
        parser.add_argument('--force', action='store_true', help='Force regenerate all alerts')

    def handle(self, *args, **options):
        gym_id = options.get('gym_id')
        force = options.get('force')
        
        self.stdout.write("Starting automatic alert generation...")
        
        # Filter by gym if specified
        inventory_filter = {}
        equipment_filter = {}
        
        if gym_id:
            inventory_filter['gym_id'] = gym_id
            equipment_filter['gym_id'] = gym_id
        
        # Check all inventory items
        inventory_items = InventoryItem.objects.filter(is_active=True, **inventory_filter)
        self.stdout.write(f"Checking {inventory_items.count()} inventory items...")
        
        for item in inventory_items:
            # Force save to trigger signals
            item.save()
        
        # Check all equipment
        equipment_items = Equipment.objects.filter(is_active=True, **equipment_filter)
        self.stdout.write(f"Checking {equipment_items.count()} equipment items...")
        
        for equipment in equipment_items:
            # Force save to trigger signals
            equipment.save()
        
        self.stdout.write(self.style.SUCCESS("Alert generation completed successfully!"))

