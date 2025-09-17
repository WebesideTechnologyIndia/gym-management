from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from multiple_gym.models import Gym  # Correct import of Gym model


class Vendor(models.Model):
    """Vendor/Supplier information"""
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15)
    alternate_phone = models.CharField(max_length=15, blank=True)
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    
    # Business details
    gst_number = models.CharField(max_length=20, blank=True)
    pan_number = models.CharField(max_length=10, blank=True)
    
    # Vendor ratings and notes
    rating = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating out of 5"
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class EquipmentCategory(models.Model):
    """Equipment categories - moved before Equipment class"""
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='category_icons/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # ADD THIS FIELD if you want to track who created the category
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Equipment Categories"
        ordering = ['name']
        unique_together = ['gym', 'name']  # Prevent duplicate category names per gym
    
    def __str__(self):
        return f"{self.name} ({self.gym.name})"


class Equipment(models.Model):
    """Main equipment model"""
    EQUIPMENT_STATUS_CHOICES = [
        ('working', 'Working'),
        ('maintenance', 'Under Maintenance'),
        ('repair', 'Under Repair'),
        ('out_of_order', 'Out of Order'),
        ('disposed', 'Disposed'),
    ]
    
    CONDITION_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('critical', 'Critical'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=100)
    category = models.ForeignKey(EquipmentCategory, on_delete=models.CASCADE, related_name='equipment')
    brand = models.CharField(max_length=100)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, unique=True)
    
    # Gym association
    gym = models.ForeignKey('multiple_gym.Gym', on_delete=models.CASCADE, related_name='equipment')
    
    # Purchase Information
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    purchase_date = models.DateField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    invoice_number = models.CharField(max_length=100, blank=True)
    
    # Warranty Information
    warranty_period_months = models.IntegerField(default=12)
    warranty_start_date = models.DateField()
    warranty_end_date = models.DateField(null=True, blank=True)
    
    # Current Status
    status = models.CharField(max_length=20, choices=EQUIPMENT_STATUS_CHOICES, default='working')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='excellent')
    location = models.CharField(max_length=100, help_text="Location within gym")
    
    # Maintenance
    last_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)
    maintenance_frequency_days = models.IntegerField(default=90, help_text="Maintenance frequency in days")
    
    # Asset Management
    depreciation_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.00, 
        help_text="Annual depreciation rate as percentage"
    )
    
    # Additional Information
    specifications = models.TextField(blank=True, help_text="Technical specifications")
    notes = models.TextField(blank=True)
    image = models.ImageField(upload_to='equipment_images/', blank=True, null=True)
    
    # Tracking
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['serial_number', 'gym']
    
    def __str__(self):
        return f"{self.name} - {self.serial_number}"
    
    @property
    def current_value(self):
        """Calculate current value after depreciation"""
        if not self.purchase_date:
            return self.purchase_price
        
        years_passed = (date.today() - self.purchase_date).days / 365.25
        depreciation_amount = (self.purchase_price * self.depreciation_rate * Decimal(str(years_passed))) / 100
        current_value = self.purchase_price - depreciation_amount
        return max(current_value, Decimal('0.00'))
    
    @property
    def is_warranty_valid(self):
        """Check if warranty is still valid"""
        return date.today() <= self.warranty_end_date if self.warranty_end_date else False
    
    @property
    def warranty_days_remaining(self):
        """Days remaining in warranty"""
        if self.is_warranty_valid:
            return (self.warranty_end_date - date.today()).days
        return 0
    
    @property
    def needs_maintenance(self):
        """Check if equipment needs maintenance"""
        if not self.next_maintenance_date:
            return False
        return date.today() >= self.next_maintenance_date
    
    @property
    def maintenance_overdue_days(self):
        """Days overdue for maintenance"""
        if self.next_maintenance_date and date.today() > self.next_maintenance_date:
            return (date.today() - self.next_maintenance_date).days
        return 0
    
    def save(self, *args, **kwargs):
        """Override save to auto-calculate dates"""
        import calendar
        from datetime import timedelta, datetime

        # Auto-calculate warranty end date
        if self.warranty_start_date and self.warranty_period_months:
            year = self.warranty_start_date.year
            month = self.warranty_start_date.month + self.warranty_period_months
            day = self.warranty_start_date.day

            # Handle year overflow
            while month > 12:
                year += 1
                month -= 12

            # Handle day overflow for months with fewer days
            max_day = calendar.monthrange(year, month)[1]
            if day > max_day:
                day = max_day

            self.warranty_end_date = datetime(year, month, day).date()

        # Set next maintenance date if not set
        if not self.next_maintenance_date and self.last_maintenance_date:
            self.next_maintenance_date = self.last_maintenance_date + timedelta(days=self.maintenance_frequency_days)
        elif not self.next_maintenance_date and not self.last_maintenance_date:
            self.next_maintenance_date = self.purchase_date + timedelta(days=self.maintenance_frequency_days)

        super().save(*args, **kwargs)


# Rest of your models follow...

class MaintenanceRecord(models.Model):
    """Equipment maintenance tracking"""
    MAINTENANCE_TYPE_CHOICES = [
        ('preventive', 'Preventive Maintenance'),
        ('corrective', 'Corrective Maintenance'),
        ('emergency', 'Emergency Repair'),
        ('inspection', 'Inspection'),
        ('calibration', 'Calibration'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPE_CHOICES)
    
    # Scheduling
    scheduled_date = models.DateField()
    actual_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Details
    description = models.TextField()
    work_performed = models.TextField(blank=True)
    parts_replaced = models.TextField(blank=True)
    
    # Personnel
    technician_name = models.CharField(max_length=100, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Cost
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    parts_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Next maintenance
    next_maintenance_due = models.DateField(null=True, blank=True)
    
    # Additional
    downtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text="Equipment downtime in hours")
    notes = models.TextField(blank=True)
    before_images = models.ImageField(upload_to='maintenance_images/', blank=True, null=True)
    after_images = models.ImageField(upload_to='maintenance_images/', blank=True, null=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"{self.equipment.name} - {self.maintenance_type} ({self.scheduled_date})"
    
    def save(self, *args, **kwargs):
        try:
            # Calculate total cost
            self.total_cost = self.labor_cost + self.parts_cost
            
            # AUTO UPDATE EQUIPMENT STATUS based on maintenance status
            if self.status == 'scheduled':
                self.equipment.status = 'maintenance'
                self.equipment.save()
                
            elif self.status == 'in_progress':
                self.equipment.status = 'maintenance' 
                self.equipment.save()
                
            elif self.status == 'completed' and self.actual_date:
                self.equipment.status = 'working'
                self.equipment.last_maintenance_date = self.actual_date
                
                if self.next_maintenance_due:
                    self.equipment.next_maintenance_date = self.next_maintenance_due
                else:
                    from datetime import timedelta
                    next_date = self.actual_date + timedelta(days=self.equipment.maintenance_frequency_days)
                    self.equipment.next_maintenance_date = next_date
                
                self.equipment.save()
                
            elif self.status == 'cancelled':
                if self.equipment.status == 'maintenance':
                    self.equipment.status = 'working'
                    self.equipment.save()
            
            super().save(*args, **kwargs)
            
        except Exception as e:
            print(f"❌ Error in MaintenanceRecord save: {str(e)}")
            raise e


class InventoryCategory(models.Model):
    """Categories for inventory items"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Inventory Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    """Inventory items like supplements, towels, etc."""
    UNIT_CHOICES = [
        ('piece', 'Piece'),
        ('kg', 'Kilogram'),
        ('liter', 'Liter'),
        ('packet', 'Packet'),
        ('bottle', 'Bottle'),
        ('box', 'Box'),
        ('meter', 'Meter'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=100)
    category = models.ForeignKey(InventoryCategory, on_delete=models.CASCADE, related_name='items')
    brand = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    
    # Fixed: Changed from CharField to ForeignKey
    gym = models.ForeignKey('multiple_gym.Gym', on_delete=models.CASCADE, related_name='inventory_items')
    
    # Stock Information
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    maximum_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='piece')
    
    # Pricing
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Auto reorder
    auto_reorder = models.BooleanField(default=False)
    reorder_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Vendor
    primary_vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Additional
    sku = models.CharField(max_length=50, unique=True, blank=True)
    barcode = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=100, blank=True, help_text="Storage location")
    
    # Expiry tracking (for supplements, etc.)
    has_expiry = models.BooleanField(default=False)
    expiry_alert_days = models.IntegerField(default=30, help_text="Alert X days before expiry")
    
    # Tracking
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['name', 'gym']
    
    def __str__(self):
        return f"{self.name} ({self.current_stock} {self.unit})"
    
    @property
    def is_low_stock(self):
        """Check if stock is below minimum level"""
        return self.current_stock <= self.minimum_stock
    
    @property
    def stock_percentage(self):
        """Calculate stock percentage based on min/max levels"""
        if self.maximum_stock <= self.minimum_stock:
            return 100 if self.current_stock > 0 else 0
        
        if self.current_stock <= self.minimum_stock:
            return 0
        elif self.current_stock >= self.maximum_stock:
            return 100
        else:
            # Calculate percentage between min and max
            range_stock = self.maximum_stock - self.minimum_stock
            current_above_min = self.current_stock - self.minimum_stock
            return (current_above_min / range_stock) * 100
    
    @property
    def total_value(self):
        """Calculate total stock value"""
        return self.current_stock * self.cost_price



class StockTransaction(models.Model):
    """Track all stock movements - FIXED VERSION"""
    TRANSACTION_TYPE_CHOICES = [
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('adjustment', 'Stock Adjustment'),
        ('damage', 'Damage/Loss'),
        ('return', 'Return'),
        ('transfer', 'Transfer'),
        ('expired', 'Expired'),
    ]
    
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Before and after stock levels
    stock_before = models.DecimalField(max_digits=10, decimal_places=2)
    stock_after = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Reference information
    reference_number = models.CharField(max_length=100, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Expiry tracking
    expiry_date = models.DateField(null=True, blank=True)
    batch_number = models.CharField(max_length=50, blank=True)
    
    # Additional
    notes = models.TextField(blank=True)
    
    # Tracking
    transaction_date = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-transaction_date']
    
    def __str__(self):
        return f"{self.item.name} - {self.transaction_type} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        """Override save with proper Decimal handling"""
        try:
            # Convert all values to Decimal with proper validation
            if self.quantity is not None:
                quantity_decimal = Decimal(str(self.quantity))
            else:
                quantity_decimal = Decimal('0')

            if self.unit_price is not None:
                unit_price_decimal = Decimal(str(self.unit_price))
            else:
                unit_price_decimal = Decimal('0')

            if self.stock_before is not None:
                stock_before_decimal = Decimal(str(self.stock_before))
            else:
                stock_before_decimal = Decimal('0')

            # Calculate total amount using Decimal arithmetic only
            self.total_amount = quantity_decimal * unit_price_decimal

            # Update stock levels based on transaction type
            if self.transaction_type in ['purchase', 'adjustment', 'return']:
                # Incoming stock
                stock_after_decimal = stock_before_decimal + quantity_decimal
            else:  # sale, damage, transfer, expired
                # Outgoing stock
                stock_after_decimal = stock_before_decimal - quantity_decimal

                # Prevent negative stock
                if stock_after_decimal < Decimal('0'):
                    stock_after_decimal = Decimal('0')

            # Ensure stock_after is set as Decimal
            self.stock_after = stock_after_decimal

            # Call parent save first to create the transaction record
            super().save(*args, **kwargs)

            # Then update the inventory item's current stock
            # Refresh the item from database to avoid stale data
            self.item.refresh_from_db()
            self.item.current_stock = stock_after_decimal
            self.item.save(update_fields=['current_stock'])

        except Exception as e:
            print(f"❌ Error in StockTransaction.save(): {str(e)}")
            print(f"❌ Debug - quantity: {self.quantity} ({type(self.quantity)})")
            print(f"❌ Debug - unit_price: {self.unit_price} ({type(self.unit_price)})")
            print(f"❌ Debug - stock_before: {self.stock_before} ({type(self.stock_before)})")
            raise e






class StockAlert(models.Model):
    """System alerts for inventory management"""
    ALERT_TYPE_CHOICES = [
        ('low_stock', 'Low Stock'),
        ('expiry_soon', 'Expiring Soon'),
        ('expired', 'Expired'),
        ('maintenance_due', 'Maintenance Due'),
        ('warranty_expiring', 'Warranty Expiring'),
        ('reorder_needed', 'Reorder Needed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Related objects
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True, blank=True)
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, null=True, blank=True)
    
    # Alert details
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Status
    is_read = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts')
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.alert_type}: {self.title}"