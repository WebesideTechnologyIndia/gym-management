from django.core.management.base import BaseCommand
from decimal import Decimal
from datetime import date, timedelta
import uuid
from inventory_management.models import (
    InventoryItem, Equipment, InventoryCategory, 
    EquipmentCategory, Vendor
)
from multiple_gym.models import Gym


class Command(BaseCommand):
    help = 'Create test data that will automatically generate alerts'

    def add_arguments(self, parser):
        parser.add_argument('--gym-id', type=int, required=True, help='Gym ID to create test data for')
        parser.add_argument('--clean', action='store_true', help='Clean existing test data first')

    def handle(self, *args, **options):
        gym_id = options['gym_id']
        clean_first = options.get('clean', False)
        
        try:
            gym = Gym.objects.get(id=gym_id)
        except Gym.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Gym with ID {gym_id} not found'))
            return
        
        self.stdout.write(f'Creating test data for gym: {gym.name}')
        
        # Clean existing test data if requested
        if clean_first:
            InventoryItem.objects.filter(name__startswith='Test -').delete()
            Equipment.objects.filter(name__startswith='Test -').delete()
            self.stdout.write('Cleaned existing test data')
        
        # Create test inventory category
        category, _ = InventoryCategory.objects.get_or_create(
            name='Test Supplements & Supplies'
        )
        
        # Create test vendor
        vendor, _ = Vendor.objects.get_or_create(
            name='Test Fitness Supplier',
            defaults={
                'phone': '9876543210',
                'address': 'Test Address, Test City',
                'city': 'Test City',
                'state': 'Test State',
                'pincode': '123456',
                'email': 'supplier@test.com'
            }
        )
        
        # Create LOW STOCK inventory items that will trigger alerts
        low_stock_items = [
            {
                'name': f'Test - Whey Protein Powder G{gym_id}',
                'current_stock': Decimal('0'),  # OUT OF STOCK - Critical alert
                'minimum_stock': Decimal('10'),
                'unit': 'kg',
                'sku': f'WPP-G{gym_id}-{uuid.uuid4().hex[:6].upper()}'
            },
            {
                'name': f'Test - Gym Towels Clean G{gym_id}',
                'current_stock': Decimal('3'),  # Low stock - High alert
                'minimum_stock': Decimal('20'), 
                'unit': 'piece',
                'sku': f'GTC-G{gym_id}-{uuid.uuid4().hex[:6].upper()}'
            },
            {
                'name': f'Test - Pre-Workout Supplement G{gym_id}',
                'current_stock': Decimal('2'),  # Very low - Critical alert
                'minimum_stock': Decimal('8'),
                'unit': 'bottle',
                'sku': f'PWS-G{gym_id}-{uuid.uuid4().hex[:6].upper()}'
            },
            {
                'name': f'Test - Energy Bars G{gym_id}',
                'current_stock': Decimal('5'),  # Low stock - High alert
                'minimum_stock': Decimal('15'),
                'unit': 'box',
                'sku': f'EBA-G{gym_id}-{uuid.uuid4().hex[:6].upper()}'
            }
        ]
        
        created_items = 0
        for item_data in low_stock_items:
            try:
                item, created = InventoryItem.objects.get_or_create(
                    name=item_data['name'],
                    gym=gym,
                    defaults={
                        'category': category,
                        'current_stock': item_data['current_stock'],
                        'minimum_stock': item_data['minimum_stock'],
                        'maximum_stock': item_data['minimum_stock'] * 3,
                        'unit': item_data['unit'],
                        'cost_price': Decimal('150'),
                        'selling_price': Decimal('200'),
                        'auto_reorder': True,
                        'reorder_quantity': item_data['minimum_stock'] * 2,
                        'primary_vendor': vendor,
                        'sku': item_data['sku']
                    }
                )
                
                if created:
                    created_items += 1
                    self.stdout.write(f'✅ Created: {item.name} (Stock: {item.current_stock}/{item.minimum_stock})')
                else:
                    # Update existing item to trigger alerts
                    item.current_stock = item_data['current_stock']
                    item.minimum_stock = item_data['minimum_stock']
                    item.save()  # This will trigger alert generation
                    self.stdout.write(f'📝 Updated: {item.name} (Stock: {item.current_stock}/{item.minimum_stock})')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating {item_data["name"]}: {e}'))
        
        # Create equipment category
        eq_category, _ = EquipmentCategory.objects.get_or_create(
            name='Test Gym Equipment',
            gym=gym
        )
        
        # Create MAINTENANCE DUE equipment that will trigger alerts
        maintenance_equipment = [
            {
                'name': f'Test - Treadmill Pro Max G{gym_id}',
                'serial_number': f'TM001-G{gym_id}-{uuid.uuid4().hex[:4].upper()}',
                'next_maintenance_date': date.today() - timedelta(days=5),  # 5 days overdue
                'warranty_end_date': date.today() + timedelta(days=45)
            },
            {
                'name': f'Test - Multi-Station Gym G{gym_id}',
                'serial_number': f'MSG002-G{gym_id}-{uuid.uuid4().hex[:4].upper()}', 
                'next_maintenance_date': date.today(),  # Due today
                'warranty_end_date': date.today() + timedelta(days=10)  # Expires in 10 days
            },
            {
                'name': f'Test - Rowing Machine Elite G{gym_id}',
                'serial_number': f'RM003-G{gym_id}-{uuid.uuid4().hex[:4].upper()}',
                'next_maintenance_date': date.today() + timedelta(days=2),  # Due in 2 days
                'warranty_end_date': date.today() + timedelta(days=5)  # Expires in 5 days - Critical
            }
        ]
        
        created_equipment = 0
        for eq_data in maintenance_equipment:
            try:
                equipment, created = Equipment.objects.get_or_create(
                    serial_number=eq_data['serial_number'],
                    defaults={
                        'name': eq_data['name'],
                        'category': eq_category,
                        'brand': 'Test Fitness Brand',
                        'gym': gym,
                        'purchase_date': date.today() - timedelta(days=365),
                        'purchase_price': Decimal('75000'),
                        'warranty_start_date': date.today() - timedelta(days=365),
                        'warranty_period_months': 12,
                        'warranty_end_date': eq_data['warranty_end_date'],
                        'vendor': vendor,
                        'location': 'Main Workout Area',
                        'next_maintenance_date': eq_data['next_maintenance_date'],
                        'maintenance_frequency_days': 90
                    }
                )
                
                if created:
                    created_equipment += 1
                    self.stdout.write(f'✅ Created: {equipment.name} (Maintenance: {equipment.next_maintenance_date})')
                else:
                    # Update existing equipment to trigger alerts
                    equipment.next_maintenance_date = eq_data['next_maintenance_date']
                    equipment.warranty_end_date = eq_data['warranty_end_date']
                    equipment.save()  # This will trigger alert generation
                    self.stdout.write(f'📝 Updated: {equipment.name} (Maintenance: {equipment.next_maintenance_date})')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating {eq_data["name"]}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'✅ Created {created_items} inventory items and {created_equipment} equipment!'))
        self.stdout.write('🔔 Alerts should be generated automatically. Check your alerts page!')
        self.stdout.write(f'🌐 Visit: /inventory/alerts/{gym_id}/')