# inventory_management/forms.py
from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import (
    Equipment,
    EquipmentCategory,
    Vendor,
    MaintenanceRecord,
    InventoryItem,
    InventoryCategory,
    StockTransaction,
)

# forms.py
from django import forms
from .models import Equipment, EquipmentCategory, Vendor


from datetime import datetime
import calendar


class EquipmentForm(forms.ModelForm):
    """Form for adding/editing equipment"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Load categories and vendors
        self.fields["category"].queryset = EquipmentCategory.objects.all().order_by("name")
        self.fields["vendor"].queryset = Vendor.objects.filter(is_active=True).order_by("name")

        # Set empty labels
        self.fields["category"].empty_label = "Select Category"
        self.fields["vendor"].empty_label = "Select Vendor (Optional)"

        # Set initial values
        if not self.instance.pk:
            self.fields["warranty_period_months"].initial = 12
            self.fields["status"].initial = "working"
            self.fields["condition"].initial = "excellent"

    class Meta:
        model = Equipment
        fields = [
            "name",
            "category", 
            "brand",
            "model_number",
            "serial_number",
            "vendor",
            "purchase_date",
            "purchase_price",
            "invoice_number",
            "warranty_period_months",
            "warranty_start_date",
            "warranty_end_date",  # WARRANTY END DATE FIELD ADD KI
            "status",
            "condition",
            "location",
            "specifications",
            "notes",
            "image",
        ]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "required": True}),
            "category": forms.Select(attrs={"class": "form-select", "required": True}),
            "brand": forms.TextInput(attrs={"class": "form-control", "required": True}),
            "model_number": forms.TextInput(attrs={"class": "form-control"}),
            "serial_number": forms.TextInput(attrs={"class": "form-control", "required": True}),
            "vendor": forms.Select(attrs={"class": "form-select"}),
            "purchase_date": forms.DateInput(attrs={"class": "form-control", "type": "date", "required": True}),
            "purchase_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "required": True}),
            "invoice_number": forms.TextInput(attrs={"class": "form-control"}),
            "warranty_period_months": forms.NumberInput(attrs={"class": "form-control", "min": "1", "max": "120", "required": True}),
            "warranty_start_date": forms.DateInput(attrs={"class": "form-control", "type": "date", "required": True}),
            "warranty_end_date": forms.DateInput(attrs={"class": "form-control", "type": "date", "required": True}),  # REQUIRED FIELD
            "status": forms.Select(attrs={"class": "form-select"}),
            "condition": forms.Select(attrs={"class": "form-select"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "specifications": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "image": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
        }

    def clean_serial_number(self):
        serial_number = self.cleaned_data.get("serial_number")
        if serial_number:
            return serial_number.upper()
        return serial_number

    def clean_warranty_end_date(self):
        """Validate warranty end date"""
        start_date = self.cleaned_data.get("warranty_start_date")
        end_date = self.cleaned_data.get("warranty_end_date")
        
        if start_date and end_date:
            if end_date <= start_date:
                raise forms.ValidationError("Warranty end date must be after start date!")
        
        return end_date



class EquipmentCategoryForm(forms.ModelForm):
    """Form for equipment categories"""

    class Meta:
        model = EquipmentCategory
        fields = ["name", "description", "icon"]

        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Category name"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Category description",
                }
            ),
            "icon": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Font Awesome icon class (e.g., fas fa-dumbbell)",
                }
            ),
        }


class VendorForm(forms.ModelForm):
    """Form for vendors/suppliers"""

    class Meta:
        model = Vendor
        fields = [
            "name",
            "contact_person",
            "email",
            "phone",
            "alternate_phone",
            "address",
            "city",
            "state",
            "pincode",
            "gst_number",
            "pan_number",
            "rating",
            "notes",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Vendor name"}
            ),
            "contact_person": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Contact person name"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Email address"}
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phone number",
                    "maxlength": "15",
                }
            ),
            "alternate_phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Alternate phone number",
                    "maxlength": "15",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Complete address",
                }
            ),
            "city": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "City"}
            ),
            "state": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "State"}
            ),
            "pincode": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "PIN Code",
                    "maxlength": "10",
                }
            ),
            "gst_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "GST Number",
                    "maxlength": "20",
                }
            ),
            "pan_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "PAN Number",
                    "maxlength": "10",
                }
            ),
            "rating": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Additional notes about vendor",
                }
            ),
        }


class MaintenanceRecordForm(forms.ModelForm):
    """Form for maintenance records"""

    class Meta:
        model = MaintenanceRecord
        fields = [
            "equipment",
            "maintenance_type",
            "scheduled_date",
            "description",
            "technician_name",
            "vendor",
            "status",
        ]

        widgets = {
            "equipment": forms.Select(attrs={"class": "form-select"}),
            "maintenance_type": forms.Select(attrs={"class": "form-select"}),
            "scheduled_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Describe the maintenance work to be performed",
                }
            ),
            "technician_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Technician name"}
            ),
            "vendor": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }


class MaintenanceUpdateForm(forms.ModelForm):
    """Form for updating maintenance records"""

    class Meta:
        model = MaintenanceRecord
        fields = [
            "status",
            "actual_date",
            "work_performed",
            "parts_replaced",
            "labor_cost",
            "parts_cost",
            "downtime_hours",
            "next_maintenance_due",
            "notes",
        ]

        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
            "actual_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "work_performed": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Describe the work that was performed",
                }
            ),
            "parts_replaced": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "List parts that were replaced",
                }
            ),
            "labor_cost": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "parts_cost": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "downtime_hours": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.5", "min": "0"}
            ),
            "next_maintenance_due": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Additional notes",
                }
            ),
        }


class InventoryItemForm(forms.ModelForm):
    """Form for inventory items"""

    class Meta:
        model = InventoryItem
        fields = [
            "name",
            "category",
            "brand",
            "description",
            "current_stock",
            "minimum_stock",
            "maximum_stock",
            "unit",
            "cost_price",
            "selling_price",
            "auto_reorder",
            "reorder_quantity",
            "primary_vendor",
            "sku",
            "barcode",
            "location",
            "has_expiry",
            "expiry_alert_days",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Item name"}
            ),
            "category": forms.Select(attrs={"class": "form-select"}),
            "brand": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Brand name"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Item description",
                }
            ),
            "current_stock": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "minimum_stock": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "maximum_stock": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "unit": forms.Select(attrs={"class": "form-select"}),
            "cost_price": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "selling_price": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "auto_reorder": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "reorder_quantity": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "primary_vendor": forms.Select(attrs={"class": "form-select"}),
            "sku": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "SKU/Product code"}
            ),
            "barcode": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Barcode"}
            ),
            "location": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Storage location"}
            ),
            "has_expiry": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "expiry_alert_days": forms.NumberInput(
                attrs={"class": "form-control", "min": "1", "max": "365"}
            ),
        }


class InventoryCategoryForm(forms.ModelForm):
    """Form for inventory categories"""

    class Meta:
        model = InventoryCategory
        fields = ["name", "description", "icon"]

        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Category name"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Category description",
                }
            ),
            "icon": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Font Awesome icon class",
                }
            ),
        }


class StockTransactionForm(forms.ModelForm):
    """Form for stock transactions"""

    class Meta:
        model = StockTransaction
        fields = [
            "transaction_type",
            "quantity",
            "unit_price",
            "reference_number",
            "vendor",
            "expiry_date",
            "batch_number",
            "notes",
        ]

        widgets = {
            "transaction_type": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0.01"}
            ),
            "unit_price": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "reference_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Invoice/Receipt number"}
            ),
            "vendor": forms.Select(attrs={"class": "form-select"}),
            "expiry_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "batch_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Batch/Lot number"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Additional notes",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        item = kwargs.pop("item", None)
        super().__init__(*args, **kwargs)

        if item:
            # Set initial unit price based on item's cost/selling price
            if self.initial.get("transaction_type") in ["purchase", "adjustment"]:
                self.fields["unit_price"].initial = item.cost_price
            elif self.initial.get("transaction_type") == "sale":
                self.fields["unit_price"].initial = item.selling_price


class EquipmentSearchForm(forms.Form):
    """Form for equipment search and filtering"""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Search equipment..."}
        ),
    )

    category = forms.ModelChoiceField(
        queryset=EquipmentCategory.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    status = forms.ChoiceField(
        choices=[("", "All Status")] + Equipment.EQUIPMENT_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    condition = forms.ChoiceField(
        choices=[("", "All Conditions")] + Equipment.CONDITION_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class InventorySearchForm(forms.Form):
    """Form for inventory search and filtering"""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Search inventory..."}
        ),
    )

    category = forms.ModelChoiceField(
        queryset=InventoryCategory.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    stock_filter = forms.ChoiceField(
        choices=[
            ("", "All Items"),
            ("low_stock", "Low Stock"),
            ("out_of_stock", "Out of Stock"),
        ],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class MaintenanceSearchForm(forms.Form):
    """Form for maintenance search and filtering"""

    status = forms.ChoiceField(
        choices=[("", "All Status")] + MaintenanceRecord.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    maintenance_type = forms.ChoiceField(
        choices=[("", "All Types")] + MaintenanceRecord.MAINTENANCE_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )


class BulkStockUpdateForm(forms.Form):
    """Form for bulk stock updates"""

    items = forms.CharField(widget=forms.HiddenInput())

    adjustment_type = forms.ChoiceField(
        choices=[
            ("increase", "Increase Stock"),
            ("decrease", "Decrease Stock"),
            ("set", "Set Stock Level"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    quantity = forms.DecimalField(
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )

    reason = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Reason for bulk update",
            }
        )
    )
