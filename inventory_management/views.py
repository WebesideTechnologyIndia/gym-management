# inventory_management/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

# Import your models and forms
from .models import (
    Equipment,
    EquipmentCategory,
    Vendor,
    MaintenanceRecord,
    InventoryItem,
    InventoryCategory,
    StockTransaction,
    StockAlert,
)

# Import Gym and GymAdmin from your main app
from multiple_gym.models import Gym, GymAdmin


# Fixed Dashboard View - Replace your existing inventory_dashboard function


@login_required
def inventory_dashboard(request, gym_id=None):
    """Main inventory dashboard with alerts"""
    if request.user.user_type not in ["superadmin", "gymadmin"]:
        messages.error(request, "Access denied!")
        return redirect("login")

    # Get gym context
    gym = None
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            gym = get_object_or_404(Gym, id=gym_id)
            # Check if this gym belongs to the current admin
            if gym not in gym_admin.gyms.all():
                messages.error(request, "You do not have access to this gym!")
                return redirect("gymadmin_home")
        except GymAdmin.DoesNotExist:
            messages.error(request, "Gym admin profile not found!")
            return redirect("login")
    elif gym_id:
        gym = get_object_or_404(Gym, id=gym_id)

    # Equipment Statistics
    total_equipment = Equipment.objects.filter(gym=gym, is_active=True).count()
    working_equipment = Equipment.objects.filter(gym=gym, status="working").count()
    maintenance_due = Equipment.objects.filter(
        gym=gym, next_maintenance_date__lte=date.today()
    ).count()

    # Inventory Statistics
    total_inventory_items = InventoryItem.objects.filter(
        gym=gym, is_active=True
    ).count()
    low_stock_items = InventoryItem.objects.filter(
        gym=gym, current_stock__lte=F("minimum_stock")
    ).count()

    # Financial Statistics
    total_equipment_value = (
        Equipment.objects.filter(gym=gym, is_active=True).aggregate(
            total=Sum("purchase_price")
        )["total"]
        or 0
    )

    total_inventory_value = sum(
        item.total_value
        for item in InventoryItem.objects.filter(gym=gym, is_active=True)
    )

    # Recent Activity
    recent_maintenance = MaintenanceRecord.objects.filter(equipment__gym=gym).order_by(
        "-created_at"
    )[:5]

    recent_transactions = StockTransaction.objects.filter(item__gym=gym).order_by(
        "-transaction_date"
    )[:5]

    # 🔥 FIXED: Get all alerts first, then calculate counts BEFORE slicing
    all_alerts = StockAlert.objects.filter(
        Q(equipment__gym=gym) | Q(inventory_item__gym=gym), is_resolved=False
    ).order_by("-created_at")

    # Calculate alert counts BEFORE slicing
    critical_alerts = all_alerts.filter(priority="critical").count()
    high_alerts = all_alerts.filter(priority="high").count()

    # Now slice for display (only first 10)
    alerts = all_alerts[:10]

    context = {
        "gym": gym,
        "gym_id": gym_id,
        "total_equipment": total_equipment,
        "working_equipment": working_equipment,
        "maintenance_due": maintenance_due,
        "total_inventory_items": total_inventory_items,
        "low_stock_items": low_stock_items,
        "total_equipment_value": total_equipment_value,
        "total_inventory_value": total_inventory_value,
        "recent_maintenance": recent_maintenance,
        "recent_transactions": recent_transactions,
        "alerts": alerts,
        "critical_alerts": critical_alerts,
        "high_alerts": high_alerts,
    }

    return render(request, "inventory_management/dashboard.html", context)


def equipment_list(request, gym_id):
    """Equipment list view with simple debugging"""

    # Basic permission check
    if request.user.user_type not in ["superadmin", "gymadmin"]:
        messages.error(request, "Access denied!")
        return redirect("login")

    # Get gym
    gym = get_object_or_404(Gym, id=gym_id)
    print(f"🔍 Debug - Gym found: {gym.name} (ID: {gym.id})")

    # Check if any equipment exists at all
    all_equipment = Equipment.objects.all()
    print(f"🔍 Debug - Total equipment in database: {all_equipment.count()}")

    for eq in all_equipment:
        print(f"  - {eq.name} (Gym: '{eq.gym}', Type: {type(eq.gym)})")

    # Try different filtering approaches
    print(f"🔍 Debug - Looking for equipment with gym='{gym}'")

    # Method 1: Filter by gym object
    equipment_list = Equipment.objects.filter(gym=gym)
    print(f"🔍 Debug - Method 1 (gym object): Found {equipment_list.count()} equipment")

    # Method 2: Filter by gym string (if gym is CharField)
    equipment_list2 = Equipment.objects.filter(gym=str(gym))
    print(
        f"🔍 Debug - Method 2 (gym string): Found {equipment_list2.count()} equipment"
    )

    # Method 3: Filter by gym name
    equipment_list3 = Equipment.objects.filter(gym=gym.name)
    print(f"🔍 Debug - Method 3 (gym name): Found {equipment_list3.count()} equipment")

    # Method 4: Filter by gym ID (if gym field stores ID)
    equipment_list4 = Equipment.objects.filter(gym=str(gym.id))
    print(f"🔍 Debug - Method 4 (gym ID): Found {equipment_list4.count()} equipment")

    # Use the method that returns data
    if equipment_list.count() > 0:
        final_equipment_list = equipment_list
        print("✅ Using Method 1 (gym object)")
    elif equipment_list2.count() > 0:
        final_equipment_list = equipment_list2
        print("✅ Using Method 2 (gym string)")
    elif equipment_list3.count() > 0:
        final_equipment_list = equipment_list3
        print("✅ Using Method 3 (gym name)")
    elif equipment_list4.count() > 0:
        final_equipment_list = equipment_list4
        print("✅ Using Method 4 (gym ID)")
    else:
        final_equipment_list = Equipment.objects.none()
        print("❌ No equipment found with any method!")

    # Print each equipment found
    print(f"🔍 Debug - Final equipment list ({final_equipment_list.count()} items):")
    for equipment in final_equipment_list:
        print(f"  ✅ {equipment.name} - {equipment.brand} - {equipment.serial_number}")

    # Get categories for filter
    categories = EquipmentCategory.objects.all()
    print(f"🔍 Debug - Categories found: {categories.count()}")

    context = {
        "gym": gym,
        "gym_id": gym_id,
        "equipment_list": final_equipment_list,
        "categories": categories,
        "search_query": "",
        "category_filter": "",
        "status_filter": "",
    }

    print(f"🔍 Debug - Sending to template: {len(context['equipment_list'])} equipment")

    return render(request, "inventory_management/equipment_list.html", context)


@login_required
def equipment_detail(request, gym_id, equipment_id):
    """Equipment detail view"""
    gym = get_object_or_404(Gym, id=gym_id)
    equipment = get_object_or_404(Equipment, id=equipment_id, gym=gym)

    # Check access permissions for gymadmin
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            if gym not in gym_admin.gyms.all():
                messages.error(request, "You do not have access to this gym!")
                return redirect("gymadmin_home")
        except GymAdmin.DoesNotExist:
            messages.error(request, "Access denied!")
            return redirect("login")

    # Get maintenance history
    maintenance_history = MaintenanceRecord.objects.filter(
        equipment=equipment
    ).order_by("-scheduled_date")

    # Calculate maintenance costs
    total_maintenance_cost = (
        maintenance_history.aggregate(total=Sum("total_cost"))["total"] or 0
    )

    context = {
        "equipment": equipment,
        "maintenance_history": maintenance_history,
        "total_maintenance_cost": total_maintenance_cost,
        "gym": gym,
        "gym_id": gym_id,
    }

    return render(request, "inventory_management/equipment_detail.html", context)


# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Equipment, EquipmentCategory, Vendor
from .forms import EquipmentForm

# from your_main_app.models import Gym, GymAdmin  # Adjust import as needed

from dateutil.relativedelta import relativedelta


from dateutil.relativedelta import relativedelta


@login_required
def add_equipment(request, gym_id):
    """Add new equipment using Django form"""
    if request.user.user_type not in ["superadmin", "gymadmin"]:
        messages.error(request, "Access denied!")
        return redirect("login")

    gym = get_object_or_404(Gym, id=gym_id)

    # Check access permissions for gymadmin
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            if gym not in gym_admin.gyms.all():
                messages.error(request, "You do not have access to this gym!")
                return redirect("gymadmin_home")
        except GymAdmin.DoesNotExist:
            messages.error(request, "Access denied!")
            return redirect("login")

    if request.method == "POST":
        form = EquipmentForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Check if serial number already exists for this gym
                serial_number = form.cleaned_data["serial_number"]
                if Equipment.objects.filter(
                    gym=gym, serial_number=serial_number
                ).exists():
                    form.add_error(
                        "serial_number",
                        f"Equipment with serial number {serial_number} already exists in this gym!",
                    )
                else:
                    # Save the equipment
                    equipment = form.save(commit=False)
                    equipment.gym = gym  # Set the gym
                    equipment.created_by = request.user

                    # Ensure warranty_end_date is calculated before saving
                    if (
                        equipment.warranty_start_date
                        and equipment.warranty_period_months
                    ):
                        import calendar
                        from datetime import datetime

                        year = equipment.warranty_start_date.year
                        month = (
                            equipment.warranty_start_date.month
                            + equipment.warranty_period_months
                        )
                        day = equipment.warranty_start_date.day

                        # Handle year overflow
                        while month > 12:
                            year += 1
                            month -= 12

                        # Handle day overflow for months with fewer days
                        max_day = calendar.monthrange(year, month)[1]
                        if day > max_day:
                            day = max_day

                        equipment.warranty_end_date = datetime(year, month, day).date()

                    equipment.save()

                    messages.success(
                        request, f'Equipment "{equipment.name}" added successfully!'
                    )
                    return redirect("inventory:equipment_list", gym_id=gym_id)
            except Exception as e:
                messages.error(request, f"Error adding equipment: {str(e)}")
        else:
            # Form validation errors - they will be displayed in the template
            messages.error(request, "Please correct the errors below.")
    else:
        form = EquipmentForm()

    # Get categories and vendors for template context (if needed)
    categories = EquipmentCategory.objects.all().order_by("name")
    vendors = Vendor.objects.filter(is_active=True).order_by("name")

    context = {
        "form": form,
        "gym": gym,
        "gym_id": gym_id,
        "categories": categories,  # Add if your template needs it
        "vendors": vendors,  # Add if your template needs it
    }

    return render(request, "inventory_management/add_equipment.html", context)


# Maintenance Views
@login_required
def maintenance_list(request, gym_id=None):
    """List maintenance records"""
    gym = get_object_or_404(Gym, id=gym_id)

    # Check access permissions for gymadmin
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            if gym not in gym_admin.gyms.all():
                messages.error(request, "You do not have access to this gym!")
                return redirect("gymadmin_home")
        except GymAdmin.DoesNotExist:
            messages.error(request, "Access denied!")
            return redirect("login")

    maintenance_records = MaintenanceRecord.objects.filter(equipment__gym=gym).order_by(
        "-scheduled_date"
    )

    # Filter by status
    status_filter = request.GET.get("status")
    if status_filter:
        maintenance_records = maintenance_records.filter(status=status_filter)

    # Filter by type
    type_filter = request.GET.get("type")
    if type_filter:
        maintenance_records = maintenance_records.filter(maintenance_type=type_filter)

    context = {
        "maintenance_records": maintenance_records,
        "gym": gym,
        "gym_id": gym_id,
        "status_filter": status_filter,
        "type_filter": type_filter,
    }

    return render(request, "inventory_management/maintenance_list.html", context)


@login_required
def schedule_maintenance(request, gym_id, equipment_id=None):
    """Schedule maintenance for equipment"""
    gym = get_object_or_404(Gym, id=gym_id)
    equipment = None
    if equipment_id:
        equipment = get_object_or_404(Equipment, id=equipment_id, gym=gym)

    # Check access permissions for gymadmin
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            if gym not in gym_admin.gyms.all():
                messages.error(request, "You do not have access to this gym!")
                return redirect("gymadmin_home")
        except GymAdmin.DoesNotExist:
            messages.error(request, "Access denied!")
            return redirect("login")

    if request.method == "POST":
        try:
            maintenance = MaintenanceRecord.objects.create(
                equipment_id=request.POST.get("equipment"),
                maintenance_type=request.POST.get("maintenance_type"),
                scheduled_date=request.POST.get("scheduled_date"),
                description=request.POST.get("description"),
                technician_name=request.POST.get("technician_name", ""),
                vendor_id=(
                    request.POST.get("vendor") if request.POST.get("vendor") else None
                ),
                created_by=request.user,
            )
            messages.success(request, "Maintenance scheduled successfully!")
            return redirect("inventory:maintenance_list", gym_id=gym_id)
        except Exception as e:
            messages.error(request, f"Error scheduling maintenance: {str(e)}")

    # 🔥 DEBUG: Check what's in the database
    print(f"🔍 Debug - Gym: {gym.name} (ID: {gym.id})")

    # Try different filtering methods like in equipment_list
    all_equipment = Equipment.objects.all()
    print(f"🔍 Debug - Total equipment in database: {all_equipment.count()}")

    for eq in all_equipment:
        print(f"  - {eq.name} (Gym: '{eq.gym}', Type: {type(eq.gym)})")

    # Method 1: Filter by gym object
    equipment_list = Equipment.objects.filter(gym=gym, is_active=True)
    print(f"🔍 Debug - Method 1 (gym object): Found {equipment_list.count()} equipment")

    # Method 2: Filter by gym string (if gym is CharField)
    equipment_list2 = Equipment.objects.filter(gym=str(gym), is_active=True)
    print(
        f"🔍 Debug - Method 2 (gym string): Found {equipment_list2.count()} equipment"
    )

    # Method 3: Filter by gym name
    equipment_list3 = Equipment.objects.filter(gym=gym.name, is_active=True)
    print(f"🔍 Debug - Method 3 (gym name): Found {equipment_list3.count()} equipment")

    # Method 4: Filter by gym ID (if gym field stores ID)
    equipment_list4 = Equipment.objects.filter(gym=str(gym.id), is_active=True)
    print(f"🔍 Debug - Method 4 (gym ID): Found {equipment_list4.count()} equipment")

    # Use the method that returns data
    if equipment_list.count() > 0:
        final_equipment_list = equipment_list
        print("✅ Using Method 1 (gym object)")
    elif equipment_list2.count() > 0:
        final_equipment_list = equipment_list2
        print("✅ Using Method 2 (gym string)")
    elif equipment_list3.count() > 0:
        final_equipment_list = equipment_list3
        print("✅ Using Method 3 (gym name)")
    elif equipment_list4.count() > 0:
        final_equipment_list = equipment_list4
        print("✅ Using Method 4 (gym ID)")
    else:
        final_equipment_list = Equipment.objects.none()
        print("❌ No equipment found with any method!")

    # Print each equipment found
    print(f"🔍 Debug - Final equipment list ({final_equipment_list.count()} items):")
    for eq in final_equipment_list:
        print(f"  ✅ {eq.name} - {eq.brand} - {eq.serial_number}")

    vendors = Vendor.objects.filter(is_active=True)
    print(f"🔍 Debug - Vendors found: {vendors.count()}")

    context = {
        "equipment": equipment,
        "equipment_list": final_equipment_list,
        "vendors": vendors,
        "gym": gym,
        "gym_id": gym_id,
        "today": date.today(),  # Add today's date for template
    }

    print(f"🔍 Debug - Sending to template: {len(context['equipment_list'])} equipment")

    return render(request, "inventory_management/schedule_maintenance.html", context)


# Inventory Views


@login_required
def inventory_list(request, gym_id=None):
    """List inventory items with debugging"""
    if request.user.user_type not in ["superadmin", "gymadmin"]:
        messages.error(request, "Access denied!")
        return redirect("login")

    gym = get_object_or_404(Gym, id=gym_id)
    print(f"🔍 Debug - Gym found: {gym.name} (ID: {gym.id})")

    # Check access permissions for gymadmin
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            if gym not in gym_admin.gyms.all():
                messages.error(request, "You do not have access to this gym!")
                return redirect("gymadmin_home")
        except GymAdmin.DoesNotExist:
            messages.error(request, "Access denied!")
            return redirect("login")

    # Debug: Check all inventory items
    all_inventory = InventoryItem.objects.all()
    print(f"🔍 Debug - Total inventory items in database: {all_inventory.count()}")

    for item in all_inventory:
        print(f"  - {item.name} (Gym: '{item.gym}', Active: {item.is_active})")

    # Try different filtering approaches
    print(f"🔍 Debug - Looking for inventory with gym='{gym}' and is_active=True")

    # Method 1: Filter by gym object
    inventory_items = InventoryItem.objects.filter(gym=gym, is_active=True)
    print(f"🔍 Debug - Method 1 (gym object): Found {inventory_items.count()} items")

    # Method 2: Filter by gym string
    inventory_items2 = InventoryItem.objects.filter(gym=str(gym), is_active=True)
    print(f"🔍 Debug - Method 2 (gym string): Found {inventory_items2.count()} items")

    # Method 3: Filter by gym name
    inventory_items3 = InventoryItem.objects.filter(gym=gym.name, is_active=True)
    print(f"🔍 Debug - Method 3 (gym name): Found {inventory_items3.count()} items")

    # Method 4: Filter by gym ID
    inventory_items4 = InventoryItem.objects.filter(gym=str(gym.id), is_active=True)
    print(f"🔍 Debug - Method 4 (gym ID): Found {inventory_items4.count()} items")

    # Method 5: Just check is_active
    inventory_items5 = InventoryItem.objects.filter(is_active=True)
    print(
        f"🔍 Debug - Method 5 (only is_active): Found {inventory_items5.count()} items"
    )

    # Use the method that returns data
    if inventory_items.count() > 0:
        final_inventory_items = inventory_items
        print("✅ Using Method 1 (gym object)")
    elif inventory_items2.count() > 0:
        final_inventory_items = inventory_items2
        print("✅ Using Method 2 (gym string)")
    elif inventory_items3.count() > 0:
        final_inventory_items = inventory_items3
        print("✅ Using Method 3 (gym name)")
    elif inventory_items4.count() > 0:
        final_inventory_items = inventory_items4
        print("✅ Using Method 4 (gym ID)")
    elif inventory_items5.count() > 0:
        final_inventory_items = inventory_items5
        print("✅ Using Method 5 (only is_active) - WARNING: No gym filtering!")
    else:
        final_inventory_items = InventoryItem.objects.none()
        print("❌ No inventory items found with any method!")

    # Search functionality
    search_query = request.GET.get("search")
    if search_query:
        final_inventory_items = final_inventory_items.filter(
            Q(name__icontains=search_query)
            | Q(brand__icontains=search_query)
            | Q(sku__icontains=search_query)
        )
        print(
            f"🔍 Debug - After search '{search_query}': {final_inventory_items.count()} items"
        )

    # Filter by category
    category_filter = request.GET.get("category")
    if category_filter:
        final_inventory_items = final_inventory_items.filter(
            category__id=category_filter
        )
        print(
            f"🔍 Debug - After category filter: {final_inventory_items.count()} items"
        )

    # Filter by stock level
    stock_filter = request.GET.get("stock_filter")
    if stock_filter == "low_stock":
        final_inventory_items = final_inventory_items.filter(
            current_stock__lte=F("minimum_stock")
        )
    elif stock_filter == "out_of_stock":
        final_inventory_items = final_inventory_items.filter(current_stock=0)

    if stock_filter:
        print(
            f"🔍 Debug - After stock filter '{stock_filter}': {final_inventory_items.count()} items"
        )

    final_inventory_items = final_inventory_items.order_by("name")

    # Print each item found
    print(f"🔍 Debug - Final inventory items ({final_inventory_items.count()} items):")
    for item in final_inventory_items:
        print(
            f"  ✅ {item.name} - Stock: {item.current_stock} - Category: {getattr(item.category, 'name', 'None')}"
        )

    categories = InventoryCategory.objects.all()
    print(f"🔍 Debug - Categories found: {categories.count()}")

    # Calculate statistics with error handling
    try:
        total_value = 0
        for item in final_inventory_items:
            try:
                # Check if item has total_value property/method
                if hasattr(item, "total_value"):
                    if callable(item.total_value):
                        total_value += item.total_value()
                    else:
                        total_value += item.total_value
                else:
                    # Calculate manually
                    total_value += item.current_stock * item.cost_price
            except Exception as e:
                print(f"⚠️ Error calculating total_value for {item.name}: {e}")
                total_value += item.current_stock * item.cost_price

        low_stock_count = final_inventory_items.filter(
            current_stock__lte=F("minimum_stock")
        ).count()
        print(
            f"🔍 Debug - Statistics: Total Value: ₹{total_value}, Low Stock: {low_stock_count}"
        )

    except Exception as e:
        print(f"⚠️ Error calculating statistics: {e}")
        total_value = 0
        low_stock_count = 0

    context = {
        "inventory_items": final_inventory_items,
        "categories": categories,
        "gym": gym,
        "gym_id": gym_id,
        "search_query": search_query,
        "category_filter": category_filter,
        "stock_filter": stock_filter,
        "total_value": total_value,
        "low_stock_count": low_stock_count,
    }

    print(f"🔍 Debug - Sending to template: {len(context['inventory_items'])} items")

    return render(request, "inventory_management/inventory_list.html", context)


# Vendor Views
@login_required
def vendor_list(request):
    """List all vendors"""
    vendors = Vendor.objects.all().order_by("name")

    search_query = request.GET.get("search")
    if search_query:
        vendors = vendors.filter(
            Q(name__icontains=search_query)
            | Q(contact_person__icontains=search_query)
            | Q(phone__icontains=search_query)
        )

    context = {
        "vendors": vendors,
        "search_query": search_query,
    }

    return render(request, "inventory_management/vendor_list.html", context)


@login_required
def add_vendor(request):
    """Add new vendor"""
    if request.method == "POST":
        try:
            vendor = Vendor.objects.create(
                name=request.POST.get("name"),
                contact_person=request.POST.get("contact_person", ""),
                email=request.POST.get("email", ""),
                phone=request.POST.get("phone"),
                alternate_phone=request.POST.get("alternate_phone", ""),
                address=request.POST.get("address"),
                city=request.POST.get("city"),
                state=request.POST.get("state"),
                pincode=request.POST.get("pincode"),
                gst_number=request.POST.get("gst_number", ""),
                pan_number=request.POST.get("pan_number", ""),
                rating=request.POST.get("rating", 5),
                notes=request.POST.get("notes", ""),
            )
            messages.success(request, "Vendor added successfully!")
            return redirect("inventory:vendor_list")
        except Exception as e:
            messages.error(request, f"Error adding vendor: {str(e)}")

    return render(request, "inventory_management/add_vendor.html")


# Simplified placeholder views for other functionality
@login_required
def inventory_detail(request, gym_id, item_id):
    """Placeholder for inventory detail"""
    messages.info(request, "Inventory detail view coming soon!")
    return redirect("inventory:inventory_list", gym_id=gym_id)


@login_required
def add_inventory_item(request, gym_id):
    """Placeholder for add inventory item"""
    messages.info(request, "Add inventory item feature coming soon!")
    return redirect("inventory:inventory_list", gym_id=gym_id)


@login_required
def stock_transaction(request, gym_id, item_id):
    """Placeholder for stock transaction"""
    messages.info(request, "Stock transaction feature coming soon!")
    return redirect("inventory:inventory_list", gym_id=gym_id)


@login_required
def update_maintenance(request, gym_id, maintenance_id):
    """Placeholder for update maintenance"""
    messages.info(request, "Update maintenance feature coming soon!")
    return redirect("inventory:maintenance_list", gym_id=gym_id)


@login_required
def equipment_reports(request, gym_id):
    """Placeholder for equipment reports"""
    messages.info(request, "Equipment reports coming soon!")
    return redirect("inventory:dashboard", gym_id=gym_id)


@login_required
def inventory_reports(request, gym_id):
    """Placeholder for inventory reports"""
    messages.info(request, "Inventory reports coming soon!")
    return redirect("inventory:dashboard", gym_id=gym_id)


@login_required
def alerts_view(request, gym_id=None):
    """Placeholder for alerts view"""
    messages.info(request, "Alerts view coming soon!")
    return redirect("inventory:dashboard", gym_id=gym_id)


@login_required
def resolve_alert(request, alert_id):
    """Placeholder for resolve alert"""
    messages.info(request, "Resolve alert feature coming soon!")
    return redirect("inventory:dashboard")


@login_required
def get_equipment_maintenance_data(request, equipment_id):
    """AJAX view to get equipment maintenance data"""
    equipment = get_object_or_404(Equipment, id=equipment_id)

    data = {
        "last_maintenance": (
            equipment.last_maintenance_date.isoformat()
            if equipment.last_maintenance_date
            else None
        ),
        "next_maintenance": (
            equipment.next_maintenance_date.isoformat()
            if equipment.next_maintenance_date
            else None
        ),
        "maintenance_frequency": equipment.maintenance_frequency_days,
        "current_condition": equipment.condition,
        "status": equipment.status,
    }

    return JsonResponse(data)


@login_required
def get_inventory_item_data(request, item_id):
    """AJAX view to get inventory item data"""
    item = get_object_or_404(InventoryItem, id=item_id)

    data = {
        "current_stock": float(item.current_stock),
        "minimum_stock": float(item.minimum_stock),
        "maximum_stock": float(item.maximum_stock),
        "cost_price": float(item.cost_price),
        "selling_price": float(item.selling_price),
        "is_low_stock": item.is_low_stock,
        "stock_percentage": item.stock_percentage,
        "total_value": float(item.total_value),
    }

    return JsonResponse(data)


# Equipment Views
def equipment_list(request, gym_id):
    """Equipment list view with proper gym handling"""

    # Basic permission check
    if request.user.user_type not in ["superadmin", "gymadmin"]:
        messages.error(request, "Access denied!")
        return redirect("login")

    # 🔥 FIXED: Handle gym_id properly
    try:
        gym = get_object_or_404(Gym, id=gym_id)
        print(f"🔍 Debug - Gym found: {gym.name} (ID: {gym.id})")
    except (ValueError, Gym.DoesNotExist) as e:
        print(f"🔍 Debug - Error getting gym: {e}")
        messages.error(request, "Invalid gym!")
        return redirect("login")

    # Check access permissions for gymadmin
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            if gym not in gym_admin.gyms.all():
                messages.error(request, "You do not have access to this gym!")
                return redirect("gymadmin_home")
        except GymAdmin.DoesNotExist:
            messages.error(request, "Access denied!")
            return redirect("login")

    # 🔥 FIXED: Simple equipment filtering - gym is ForeignKey now
    try:
        equipment_list = Equipment.objects.filter(gym=gym, is_active=True)
        print(f"🔍 Debug - Found {equipment_list.count()} equipment for gym {gym.name}")

        # Debug each equipment
        for eq in equipment_list:
            print(f"  ✅ {eq.name} - {eq.brand} - Gym: {eq.gym.name}")

    except Exception as e:
        print(f"🔍 Debug - Error filtering equipment: {e}")
        equipment_list = Equipment.objects.none()

    # Get categories for filter
    categories = EquipmentCategory.objects.all()

    # Search functionality
    search_query = request.GET.get("search", "")
    if search_query:
        equipment_list = equipment_list.filter(
            Q(name__icontains=search_query)
            | Q(brand__icontains=search_query)
            | Q(serial_number__icontains=search_query)
        )

    # Filter by category
    category_filter = request.GET.get("category")
    if category_filter:
        equipment_list = equipment_list.filter(category__id=category_filter)

    # Filter by status
    status_filter = request.GET.get("status")
    if status_filter:
        equipment_list = equipment_list.filter(status=status_filter)

    equipment_list = equipment_list.order_by("-created_at")

    context = {
        "gym": gym,
        "gym_id": gym_id,
        "equipment_list": equipment_list,
        "categories": categories,
        "search_query": search_query,
        "category_filter": category_filter,
        "status_filter": status_filter,
    }

    print(f"🔍 Debug - Sending {equipment_list.count()} equipment to template")

    return render(request, "inventory_management/equipment_list.html", context)


@login_required
def equipment_detail(request, gym_id, equipment_id):
    """Equipment detail view"""
    equipment = get_object_or_404(Equipment, id=equipment_id, gym=str(gym_id))

    # Get maintenance history
    maintenance_history = MaintenanceRecord.objects.filter(
        equipment=equipment
    ).order_by("-scheduled_date")

    # Calculate maintenance costs
    total_maintenance_cost = (
        maintenance_history.aggregate(total=Sum("total_cost"))["total"] or 0
    )

    context = {
        "equipment": equipment,
        "maintenance_history": maintenance_history,
        "total_maintenance_cost": total_maintenance_cost,
        "gym_id": gym_id,
    }

    return render(request, "inventory_management/equipment_detail.html", context)


@login_required
def add_equipment(request, gym_id):
    """Add new equipment with detailed error handling"""
    if request.user.user_type not in ["superadmin", "gymadmin"]:
        messages.error(request, "Access denied!")
        return redirect("login")

    gym = get_object_or_404(Gym, id=gym_id)

    if request.method == "POST":
        print("POST Request received")  # Debug
        print(f"POST data: {request.POST}")  # Debug

        form = EquipmentForm(request.POST, request.FILES)

        print(f"Form is_valid: {form.is_valid()}")  # Debug

        if form.is_valid():
            print("Form is valid, trying to save...")  # Debug
            try:
                # Check serial number
                serial_number = form.cleaned_data["serial_number"]
                print(f"Serial number: {serial_number}")  # Debug

                if Equipment.objects.filter(
                    gym=gym, serial_number=serial_number
                ).exists():
                    form.add_error(
                        "serial_number",
                        f"Equipment with serial number {serial_number} already exists!",
                    )
                    print("Serial number already exists")  # Debug
                else:
                    # Print all cleaned data for debugging
                    print("Cleaned data:")
                    for key, value in form.cleaned_data.items():
                        print(f"  {key}: {value} (type: {type(value)})")

                    # Simple save
                    equipment = form.save(commit=False)
                    equipment.gym = gym
                    equipment.created_by = request.user

                    print(f"About to save equipment: {equipment}")  # Debug
                    equipment.save()

                    messages.success(
                        request, f'Equipment "{equipment.name}" added successfully!'
                    )
                    return redirect("inventory:equipment_list", gym_id=gym_id)

            except Exception as e:
                print(f"Exception occurred: {e}")  # Debug
                import traceback

                traceback.print_exc()  # Full stack trace
                messages.error(request, f"Error: {str(e)}")
        else:
            print("Form is NOT valid")  # Debug
            print(f"Form errors: {form.errors}")  # Debug
            print(f"Form non-field errors: {form.non_field_errors}")  # Debug

            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

            messages.error(request, "Please correct the errors above.")
    else:
        print("GET Request - showing blank form")  # Debug
        form = EquipmentForm()

    # Context for template
    categories = EquipmentCategory.objects.all().order_by("name")
    vendors = Vendor.objects.filter(is_active=True).order_by("name")

    context = {
        "form": form,
        "gym": gym,
        "gym_id": gym_id,
        "categories": categories,
        "vendors": vendors,
    }

    return render(request, "inventory_management/add_equipment.html", context)


# Maintenance Views
@login_required
def maintenance_list(request, gym_id=None):
    """List maintenance records"""
    maintenance_records = MaintenanceRecord.objects.filter(
        equipment__gym=str(gym_id)
    ).order_by("-scheduled_date")

    # Filter by status
    status_filter = request.GET.get("status")
    if status_filter:
        maintenance_records = maintenance_records.filter(status=status_filter)

    # Filter by type
    type_filter = request.GET.get("type")
    if type_filter:
        maintenance_records = maintenance_records.filter(maintenance_type=type_filter)

    context = {
        "maintenance_records": maintenance_records,
        "gym_id": gym_id,
        "status_filter": status_filter,
        "type_filter": type_filter,
    }

    return render(request, "inventory_management/maintenance_list.html", context)


@login_required
def schedule_maintenance(request, gym_id, equipment_id=None):
    """Schedule maintenance for equipment"""
    equipment = None
    if equipment_id:
        equipment = get_object_or_404(Equipment, id=equipment_id, gym=str(gym_id))

    if request.method == "POST":
        try:
            maintenance = MaintenanceRecord.objects.create(
                equipment_id=request.POST.get("equipment"),
                maintenance_type=request.POST.get("maintenance_type"),
                scheduled_date=request.POST.get("scheduled_date"),
                description=request.POST.get("description"),
                technician_name=request.POST.get("technician_name", ""),
                vendor_id=(
                    request.POST.get("vendor") if request.POST.get("vendor") else None
                ),
                created_by=request.user,
            )
            messages.success(request, "Maintenance scheduled successfully!")
            return redirect("maintenance_list", gym_id=gym_id)
        except Exception as e:
            messages.error(request, f"Error scheduling maintenance: {str(e)}")

    equipment_list = Equipment.objects.filter(gym=str(gym_id), is_active=True)
    vendors = Vendor.objects.filter(is_active=True)

    context = {
        "equipment": equipment,
        "equipment_list": equipment_list,
        "vendors": vendors,
        "gym_id": gym_id,
    }

    return render(request, "inventory_management/schedule_maintenance.html", context)


@login_required
def update_maintenance(request, gym_id, maintenance_id):
    """Update maintenance record"""
    gym = get_object_or_404(Gym, id=gym_id)
    maintenance = get_object_or_404(
        MaintenanceRecord, id=maintenance_id, equipment__gym=gym
    )

    # Check access permissions for gymadmin
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            if gym not in gym_admin.gyms.all():
                messages.error(request, "You do not have access to this gym!")
                return redirect("gymadmin_home")
        except GymAdmin.DoesNotExist:
            messages.error(request, "Access denied!")
            return redirect("login")

    if request.method == "POST":
        try:
            print(f"🔍 Debug - Updating maintenance: {maintenance.id}")

            # Update basic fields
            maintenance.status = request.POST.get("status")
            print(f"🔍 Debug - New status: {maintenance.status}")

            # Handle dates carefully
            actual_date_str = request.POST.get("actual_date")
            if actual_date_str:
                from datetime import datetime

                maintenance.actual_date = datetime.strptime(
                    actual_date_str, "%Y-%m-%d"
                ).date()
                print(f"🔍 Debug - Actual date: {maintenance.actual_date}")

            # Handle text fields
            maintenance.work_performed = request.POST.get("work_performed", "")
            maintenance.parts_replaced = request.POST.get("parts_replaced", "")
            maintenance.notes = request.POST.get("notes", "")

            # Handle cost fields - convert to Decimal
            from decimal import Decimal, InvalidOperation

            try:
                labor_cost_str = request.POST.get("labor_cost", "0")
                maintenance.labor_cost = (
                    Decimal(str(labor_cost_str)) if labor_cost_str else Decimal("0")
                )
            except (InvalidOperation, ValueError):
                maintenance.labor_cost = Decimal("0")

            try:
                parts_cost_str = request.POST.get("parts_cost", "0")
                maintenance.parts_cost = (
                    Decimal(str(parts_cost_str)) if parts_cost_str else Decimal("0")
                )
            except (InvalidOperation, ValueError):
                maintenance.parts_cost = Decimal("0")

            try:
                downtime_str = request.POST.get("downtime_hours", "0")
                maintenance.downtime_hours = (
                    Decimal(str(downtime_str)) if downtime_str else Decimal("0")
                )
            except (InvalidOperation, ValueError):
                maintenance.downtime_hours = Decimal("0")

            # Handle next maintenance date
            next_maintenance_str = request.POST.get("next_maintenance_due")
            if next_maintenance_str:
                from datetime import datetime

                maintenance.next_maintenance_due = datetime.strptime(
                    next_maintenance_str, "%Y-%m-%d"
                ).date()

            print(
                f"🔍 Debug - Before save: Status={maintenance.status}, Equipment={maintenance.equipment.name}"
            )

            # Save the maintenance record (this will trigger equipment status update)
            maintenance.save()

            print(
                f"🔍 Debug - After save: Equipment status={maintenance.equipment.status}"
            )

            messages.success(request, "Maintenance record updated successfully!")
            return redirect("inventory:maintenance_list", gym_id=gym_id)

        except Exception as e:
            print(f"🔍 Debug - Error in update_maintenance: {str(e)}")
            import traceback

            traceback.print_exc()
            messages.error(request, f"Error updating maintenance: {str(e)}")

    context = {
        "maintenance": maintenance,
        "gym": gym,
        "gym_id": gym_id,
    }

    return render(request, "inventory_management/update_maintenance.html", context)


# Inventory Views
# Fixed Inventory List View - Replace your existing inventory_list function


@login_required
def inventory_list(request, gym_id=None):
    """List inventory items"""
    if request.user.user_type not in ["superadmin", "gymadmin"]:
        messages.error(request, "Access denied!")
        return redirect("login")

    gym = get_object_or_404(Gym, id=gym_id)

    # Check access permissions for gymadmin
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            if gym not in gym_admin.gyms.all():
                messages.error(request, "You do not have access to this gym!")
                return redirect("gymadmin_home")
        except GymAdmin.DoesNotExist:
            messages.error(request, "Access denied!")
            return redirect("login")

    inventory_items = InventoryItem.objects.filter(gym=gym, is_active=True)

    # Search functionality
    search_query = request.GET.get("search")
    if search_query:
        inventory_items = inventory_items.filter(
            Q(name__icontains=search_query)
            | Q(brand__icontains=search_query)
            | Q(sku__icontains=search_query)
        )

    # Filter by category
    category_filter = request.GET.get("category")
    if category_filter:
        inventory_items = inventory_items.filter(category__id=category_filter)

    # Filter by stock level - 🔥 FIXED: Use F instead of models.F
    stock_filter = request.GET.get("stock_filter")
    if stock_filter == "low_stock":
        inventory_items = inventory_items.filter(current_stock__lte=F("minimum_stock"))
    elif stock_filter == "out_of_stock":
        inventory_items = inventory_items.filter(current_stock=0)

    inventory_items = inventory_items.order_by("name")
    categories = InventoryCategory.objects.all()

    # Calculate statistics - 🔥 FIXED: Use F instead of models.F
    total_value = sum(item.total_value for item in inventory_items)
    low_stock_count = inventory_items.filter(
        current_stock__lte=F("minimum_stock")
    ).count()

    context = {
        "inventory_items": inventory_items,
        "categories": categories,
        "gym": gym,
        "gym_id": gym_id,
        "search_query": search_query,
        "category_filter": category_filter,
        "stock_filter": stock_filter,
        "total_value": total_value,
        "low_stock_count": low_stock_count,
    }

    return render(request, "inventory_management/inventory_list.html", context)


@login_required
def inventory_detail(request, gym_id, item_id):
    """Inventory item detail view"""
    item = get_object_or_404(InventoryItem, id=item_id, gym=str(gym_id))

    # Get transaction history
    transactions = StockTransaction.objects.filter(item=item).order_by(
        "-transaction_date"
    )

    # Calculate statistics
    total_purchases = (
        transactions.filter(transaction_type="purchase").aggregate(
            total=Sum("quantity")
        )["total"]
        or 0
    )

    total_sales = (
        transactions.filter(transaction_type="sale").aggregate(total=Sum("quantity"))[
            "total"
        ]
        or 0
    )

    context = {
        "item": item,
        "transactions": transactions,
        "total_purchases": total_purchases,
        "total_sales": total_sales,
        "gym_id": gym_id,
    }

    return render(request, "inventory_management/inventory_detail.html", context)


@login_required
def add_inventory_item(request, gym_id):
    """Add new inventory item"""
    if request.user.user_type not in ["superadmin", "gymadmin"]:
        messages.error(request, "Access denied!")
        return redirect("login")

    if request.method == "POST":
        try:
            item = InventoryItem.objects.create(
                name=request.POST.get("name"),
                category_id=request.POST.get("category"),
                brand=request.POST.get("brand", ""),
                description=request.POST.get("description", ""),
                gym=str(gym_id),
                current_stock=request.POST.get("current_stock", 0),
                minimum_stock=request.POST.get("minimum_stock", 0),
                maximum_stock=request.POST.get("maximum_stock", 0),
                unit=request.POST.get("unit"),
                cost_price=request.POST.get("cost_price", 0),
                selling_price=request.POST.get("selling_price", 0),
                auto_reorder=request.POST.get("auto_reorder") == "on",
                reorder_quantity=request.POST.get("reorder_quantity", 0),
                primary_vendor_id=(
                    request.POST.get("vendor") if request.POST.get("vendor") else None
                ),
                sku=request.POST.get("sku", ""),
                location=request.POST.get("location", ""),
                has_expiry=request.POST.get("has_expiry") == "on",
                expiry_alert_days=request.POST.get("expiry_alert_days", 30),
                created_by=request.user,
            )

            # Create initial stock transaction if stock > 0
            if item.current_stock > 0:
                StockTransaction.objects.create(
                    item=item,
                    transaction_type="adjustment",
                    quantity=item.current_stock,
                    unit_price=item.cost_price,
                    stock_before=0,
                    stock_after=item.current_stock,
                    notes="Initial stock entry",
                    created_by=request.user,
                )

            messages.success(request, "Inventory item added successfully!")
            return redirect("inventory_list", gym_id=gym_id)
        except Exception as e:
            messages.error(request, f"Error adding inventory item: {str(e)}")

    categories = InventoryCategory.objects.all()
    vendors = Vendor.objects.filter(is_active=True)

    context = {
        "categories": categories,
        "vendors": vendors,
        "gym_id": gym_id,
    }

    return render(request, "inventory_management/add_inventory_item.html", context)


@login_required
def stock_transaction(request, gym_id, item_id):
    """Add stock transaction (purchase, sale, adjustment, etc.)"""
    item = get_object_or_404(InventoryItem, id=item_id, gym=str(gym_id))

    if request.method == "POST":
        try:
            with transaction.atomic():
                transaction_type = request.POST.get("transaction_type")
                quantity = Decimal(str(request.POST.get("quantity", 0)))
                unit_price = Decimal(str(request.POST.get("unit_price", 0)))

                # Validate quantity for outgoing transactions
                if transaction_type in ["sale", "damage", "transfer", "expired"]:
                    if quantity > item.current_stock:
                        messages.error(request, "Insufficient stock!")
                        return redirect(
                            "inventory_detail", gym_id=gym_id, item_id=item_id
                        )

                stock_transaction = StockTransaction.objects.create(
                    item=item,
                    transaction_type=transaction_type,
                    quantity=quantity,
                    unit_price=unit_price,
                    stock_before=item.current_stock,
                    reference_number=request.POST.get("reference_number", ""),
                    vendor_id=(
                        request.POST.get("vendor")
                        if request.POST.get("vendor")
                        else None
                    ),
                    expiry_date=(
                        request.POST.get("expiry_date")
                        if request.POST.get("expiry_date")
                        else None
                    ),
                    batch_number=request.POST.get("batch_number", ""),
                    notes=request.POST.get("notes", ""),
                    created_by=request.user,
                )

                messages.success(
                    request, f"Stock {transaction_type} recorded successfully!"
                )
                return redirect("inventory_detail", gym_id=gym_id, item_id=item_id)
        except Exception as e:
            messages.error(request, f"Error recording transaction: {str(e)}")

    vendors = Vendor.objects.filter(is_active=True)

    context = {
        "item": item,
        "vendors": vendors,
        "gym_id": gym_id,
    }

    return render(request, "inventory_management/stock_transaction.html", context)


# Vendor Views
@login_required
def vendor_list(request):
    """List all vendors"""
    vendors = Vendor.objects.all().order_by("name")

    search_query = request.GET.get("search")
    if search_query:
        vendors = vendors.filter(
            Q(name__icontains=search_query)
            | Q(contact_person__icontains=search_query)
            | Q(phone__icontains=search_query)
        )

    context = {
        "vendors": vendors,
        "search_query": search_query,
    }

    return render(request, "inventory_management/vendor_list.html", context)


@login_required
def add_vendor(request):
    """Add new vendor"""
    if request.method == "POST":
        try:
            vendor = Vendor.objects.create(
                name=request.POST.get("name"),
                contact_person=request.POST.get("contact_person", ""),
                email=request.POST.get("email", ""),
                phone=request.POST.get("phone"),
                alternate_phone=request.POST.get("alternate_phone", ""),
                address=request.POST.get("address"),
                city=request.POST.get("city"),
                state=request.POST.get("state"),
                pincode=request.POST.get("pincode"),
                gst_number=request.POST.get("gst_number", ""),
                pan_number=request.POST.get("pan_number", ""),
                rating=request.POST.get("rating", 5),
                notes=request.POST.get("notes", ""),
            )
            messages.success(request, "Vendor added successfully!")
            return redirect("vendor_list")
        except Exception as e:
            messages.error(request, f"Error adding vendor: {str(e)}")

    return render(request, "inventory_management/add_vendor.html")


# Reports and Analytics Views
@login_required
def equipment_reports(request, gym_id):
    """Equipment reports and analytics"""
    # Equipment by category
    equipment_by_category = (
        Equipment.objects.filter(gym=str(gym_id), is_active=True)
        .values("category__name")
        .annotate(count=Count("id"))
    )

    # Equipment by status
    equipment_by_status = (
        Equipment.objects.filter(gym=str(gym_id), is_active=True)
        .values("status")
        .annotate(count=Count("id"))
    )

    # Maintenance costs by month (last 12 months)
    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    maintenance_costs = []
    for i in range(12):
        month_start = (datetime.now() - relativedelta(months=i)).replace(day=1)
        month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)

        cost = (
            MaintenanceRecord.objects.filter(
                equipment__gym=str(gym_id),
                actual_date__range=[month_start.date(), month_end.date()],
                status="completed",
            ).aggregate(total=Sum("total_cost"))["total"]
            or 0
        )

        maintenance_costs.append(
            {"month": month_start.strftime("%b %Y"), "cost": float(cost)}
        )

    maintenance_costs.reverse()

    # Top maintenance equipment
    top_maintenance_equipment = (
        Equipment.objects.filter(gym=str(gym_id))
        .annotate(
            maintenance_count=Count("maintenance_records"),
            total_cost=Sum("maintenance_records__total_cost"),
        )
        .order_by("-total_cost")[:10]
    )

    context = {
        "gym_id": gym_id,
        "equipment_by_category": list(equipment_by_category),
        "equipment_by_status": list(equipment_by_status),
        "maintenance_costs": maintenance_costs,
        "top_maintenance_equipment": top_maintenance_equipment,
    }

    return render(request, "inventory_management/equipment_reports.html", context)


# Fixed Inventory Reports View - Replace your existing inventory_reports function


@login_required
def inventory_reports(request, gym_id):
    """Inventory reports and analytics"""
    gym = get_object_or_404(Gym, id=gym_id)

    # Check access permissions for gymadmin
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            if gym not in gym_admin.gyms.all():
                messages.error(request, "You do not have access to this gym!")
                return redirect("gymadmin_home")
        except GymAdmin.DoesNotExist:
            messages.error(request, "Access denied!")
            return redirect("login")

    # Stock value by category - 🔥 FIXED: Proper aggregation calculation
    inventory_by_category = (
        InventoryItem.objects.filter(gym=gym, is_active=True)
        .values("category__name")
        .annotate(
            total_items=Count("id"),
            total_stock=Sum("current_stock"),
            avg_cost=Sum("cost_price") / Count("id"),
            total_value=Sum(F("current_stock") * F("cost_price")),
        )
    )

    # Low stock items - 🔥 FIXED: Use F instead of models.F
    low_stock_items = InventoryItem.objects.filter(
        gym=gym, current_stock__lte=F("minimum_stock"), is_active=True
    ).order_by("current_stock")

    # Fast moving items (based on transactions)
    fast_moving_items = (
        InventoryItem.objects.filter(gym=gym, is_active=True)
        .annotate(transaction_count=Count("transactions"))
        .order_by("-transaction_count")[:10]
    )

    # Stock transactions by type (last 30 days)
    thirty_days_ago = date.today() - timedelta(days=30)
    transaction_summary = (
        StockTransaction.objects.filter(
            item__gym=gym, transaction_date__gte=thirty_days_ago
        )
        .values("transaction_type")
        .annotate(total_quantity=Sum("quantity"), total_amount=Sum("total_amount"))
    )

    # Calculate overall statistics
    total_inventory_value = (
        InventoryItem.objects.filter(gym=gym, is_active=True).aggregate(
            total=Sum(F("current_stock") * F("cost_price"))
        )["total"]
        or 0
    )

    total_items = InventoryItem.objects.filter(gym=gym, is_active=True).count()
    low_stock_count = low_stock_items.count()
    out_of_stock_count = InventoryItem.objects.filter(
        gym=gym, current_stock=0, is_active=True
    ).count()

    context = {
        "gym": gym,
        "gym_id": gym_id,
        "inventory_by_category": list(inventory_by_category),
        "low_stock_items": low_stock_items,
        "fast_moving_items": fast_moving_items,
        "transaction_summary": list(transaction_summary),
        "total_inventory_value": total_inventory_value,
        "total_items": total_items,
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
    }

    return render(request, "inventory_management/inventory_reports.html", context)


# Updated views.py - Add these functions to your existing views.py file


# Replace the existing alert views in your views.py with these FIXED versions:


@login_required
def alerts_view(request, gym_id=None):
    """View all alerts with proper filtering and statistics"""
    if request.user.user_type not in ["superadmin", "gymadmin"]:
        messages.error(request, "Access denied!")
        return redirect("login")

    gym = get_object_or_404(Gym, id=gym_id)

    # Check access permissions for gymadmin
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            if gym not in gym_admin.gyms.all():
                messages.error(request, "You do not have access to this gym!")
                return redirect("gymadmin_home")
        except GymAdmin.DoesNotExist:
            messages.error(request, "Access denied!")
            return redirect("login")

    # Get all unresolved alerts for this gym
    alerts = StockAlert.objects.filter(
        Q(equipment__gym=gym) | Q(inventory_item__gym=gym), is_resolved=False
    ).order_by("-created_at")

    # Debug: Print alert IDs
    print(f"🔍 Debug - Found {alerts.count()} alerts:")
    for alert in alerts:
        print(f"  - Alert ID: {alert.id}, Title: {alert.title}")

    # Filter by priority
    priority_filter = request.GET.get("priority")
    if priority_filter:
        alerts = alerts.filter(priority=priority_filter)

    # Filter by type
    type_filter = request.GET.get("type")
    if type_filter:
        alerts = alerts.filter(alert_type=type_filter)

    # Calculate statistics
    all_alerts = StockAlert.objects.filter(
        Q(equipment__gym=gym) | Q(inventory_item__gym=gym), is_resolved=False
    )

    critical_count = all_alerts.filter(priority="critical").count()
    high_count = all_alerts.filter(priority="high").count()

    # Resolved today count
    from datetime import datetime

    today = datetime.now().date()
    resolved_today = StockAlert.objects.filter(
        Q(equipment__gym=gym) | Q(inventory_item__gym=gym),
        is_resolved=True,
        resolved_at__date=today,
    ).count()

    context = {
        "gym": gym,
        "gym_id": gym_id,
        "alerts": alerts,
        "priority_filter": priority_filter,
        "type_filter": type_filter,
        "critical_count": critical_count,
        "high_count": high_count,
        "resolved_today": resolved_today,
    }

    return render(request, "inventory_management/alerts.html", context)


@login_required
def resolve_alert(request, gym_id, alert_id):  # 🔥 FIXED: Added gym_id parameter
    """Mark alert as resolved"""
    if request.user.user_type not in ["superadmin", "gymadmin"]:
        messages.error(request, "Access denied!")
        return redirect("login")

    gym = get_object_or_404(Gym, id=gym_id)

    try:
        alert = get_object_or_404(StockAlert, id=alert_id)
        print(f"🔍 Debug - Found alert: {alert.id} - {alert.title}")
    except:
        print(f"🔍 Debug - Alert with ID {alert_id} not found")
        messages.error(request, "Alert not found!")
        return redirect("inventory:alerts_view", gym_id=gym_id)

    # Verify alert belongs to this gym
    alert_belongs_to_gym = False
    if alert.equipment and alert.equipment.gym == gym:
        alert_belongs_to_gym = True
        print(f"🔍 Debug - Alert belongs to gym via equipment: {alert.equipment.name}")
    elif alert.inventory_item and alert.inventory_item.gym == gym:
        alert_belongs_to_gym = True
        print(
            f"🔍 Debug - Alert belongs to gym via inventory: {alert.inventory_item.name}"
        )

    if not alert_belongs_to_gym:
        print(f"🔍 Debug - Alert does not belong to gym {gym.name}")
        messages.error(request, "Alert not found!")
        return redirect("inventory:alerts_view", gym_id=gym_id)

    # Mark as resolved
    alert.is_resolved = True
    alert.resolved_by = request.user
    alert.resolved_at = timezone.now()
    alert.save()

    print(f"🔍 Debug - Alert {alert.id} marked as resolved")
    messages.success(request, f'Alert "{alert.title}" marked as resolved!')
    return redirect("inventory:alerts_view", gym_id=gym_id)


@login_required
def mark_alert_as_read(request, gym_id, alert_id):
    """AJAX view to mark alert as read"""
    if request.method == "POST" and request.user.user_type in [
        "superadmin",
        "gymadmin",
    ]:
        try:
            gym = get_object_or_404(Gym, id=gym_id)
            alert = get_object_or_404(StockAlert, id=alert_id)

            print(f"🔍 Debug - Marking alert as read: {alert.id} - {alert.title}")

            # Verify alert belongs to this gym
            alert_belongs_to_gym = False
            if alert.equipment and alert.equipment.gym == gym:
                alert_belongs_to_gym = True
            elif alert.inventory_item and alert.inventory_item.gym == gym:
                alert_belongs_to_gym = True

            if alert_belongs_to_gym:
                alert.is_read = True
                alert.save()
                print(f"🔍 Debug - Alert {alert.id} marked as read successfully")
                return JsonResponse({"success": True})
            else:
                print(f"🔍 Debug - Alert {alert.id} does not belong to gym {gym.name}")
                return JsonResponse({"success": False, "error": "Alert not found"})
        except StockAlert.DoesNotExist:
            print(f"🔍 Debug - Alert with ID {alert_id} does not exist")
            return JsonResponse({"success": False, "error": "Alert not found"})
        except Exception as e:
            print(f"🔍 Debug - Error marking alert as read: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def mark_all_alerts_as_read(request, gym_id):
    """AJAX view to mark all alerts as read"""
    if request.method == "POST" and request.user.user_type in [
        "superadmin",
        "gymadmin",
    ]:
        try:
            gym = get_object_or_404(Gym, id=gym_id)

            # Mark all unread alerts as read for this gym
            updated_count = StockAlert.objects.filter(
                Q(equipment__gym=gym) | Q(inventory_item__gym=gym),
                is_resolved=False,
                is_read=False,
            ).update(is_read=True)

            print(
                f"🔍 Debug - Marked {updated_count} alerts as read for gym {gym.name}"
            )
            return JsonResponse({"success": True, "updated_count": updated_count})
        except Exception as e:
            print(f"🔍 Debug - Error marking all alerts as read: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def resolve_all_alerts(request, gym_id):
    """AJAX view to resolve all alerts"""
    if request.method == "POST" and request.user.user_type in [
        "superadmin",
        "gymadmin",
    ]:
        try:
            gym = get_object_or_404(Gym, id=gym_id)

            # Resolve all active alerts for this gym
            alerts = StockAlert.objects.filter(
                Q(equipment__gym=gym) | Q(inventory_item__gym=gym), is_resolved=False
            )

            updated_count = alerts.update(
                is_resolved=True, resolved_by=request.user, resolved_at=timezone.now()
            )

            print(f"🔍 Debug - Resolved {updated_count} alerts for gym {gym.name}")
            return JsonResponse({"success": True, "updated_count": updated_count})
        except Exception as e:
            print(f"🔍 Debug - Error resolving all alerts: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})


# AJAX Views for dynamic content
@login_required
def get_equipment_maintenance_data(request, equipment_id):
    """AJAX view to get equipment maintenance data"""
    equipment = get_object_or_404(Equipment, id=equipment_id)

    data = {
        "last_maintenance": (
            equipment.last_maintenance_date.isoformat()
            if equipment.last_maintenance_date
            else None
        ),
        "next_maintenance": (
            equipment.next_maintenance_date.isoformat()
            if equipment.next_maintenance_date
            else None
        ),
        "maintenance_frequency": equipment.maintenance_frequency_days,
        "current_condition": equipment.condition,
        "status": equipment.status,
    }

    return JsonResponse(data)


@login_required
def get_inventory_item_data(request, item_id):
    """AJAX view to get inventory item data"""
    item = get_object_or_404(InventoryItem, id=item_id)

    data = {
        "current_stock": float(item.current_stock),
        "minimum_stock": float(item.minimum_stock),
        "maximum_stock": float(item.maximum_stock),
        "cost_price": float(item.cost_price),
        "selling_price": float(item.selling_price),
        "is_low_stock": item.is_low_stock,
        "stock_percentage": item.stock_percentage,
        "total_value": float(item.total_value),
    }

    return JsonResponse(data)


# inventory_management/views.py में add करें:


@login_required
def add_equipment_category(request):
    """Add new equipment category"""
    if request.user.user_type not in ["superadmin", "gymadmin"]:
        messages.error(request, "Access denied!")
        return redirect("login")

    if request.method == "POST":
        try:
            # Get form data
            name = request.POST.get("name", "").strip()
            description = request.POST.get("description", "").strip()
            icon = request.POST.get("icon", "").strip()

            # Validation
            if not name:
                messages.error(request, "Category name is required!")
                return render(
                    request, "inventory_management/add_equipment_category.html"
                )

            # Check if category already exists
            if EquipmentCategory.objects.filter(name__iexact=name).exists():
                messages.error(request, f'Category "{name}" already exists!')
                return render(
                    request, "inventory_management/add_equipment_category.html"
                )

            # Create category
            category = EquipmentCategory.objects.create(
                name=name, description=description, icon=icon
            )

            messages.success(
                request, f'Equipment category "{category.name}" added successfully!'
            )
            return redirect("inventory:equipment_category_list")

        except Exception as e:
            print(f"Error adding category: {str(e)}")
            messages.error(request, f"Error adding category: {str(e)}")

    # Get existing categories for reference
    existing_categories = EquipmentCategory.objects.all().order_by("name")

    context = {
        "existing_categories": existing_categories,
    }

    return render(request, "inventory_management/add_equipment_category.html", context)


@login_required
def equipment_category_list(request):
    """List all equipment categories"""
    if request.user.user_type not in ["superadmin", "gymadmin"]:
        messages.error(request, "Access denied!")
        return redirect("login")

    categories = EquipmentCategory.objects.all().order_by("name")

    # Search functionality
    search_query = request.GET.get("search", "")
    if search_query:
        categories = categories.filter(name__icontains=search_query)

    context = {
        "categories": categories,
        "search_query": search_query,
    }

    return render(request, "inventory_management/equipment_category_list.html", context)


@login_required
def edit_equipment_category(request, category_id):
    """Edit equipment category"""
    if request.user.user_type not in ["superadmin", "gymadmin"]:
        messages.error(request, "Access denied!")
        return redirect("login")

    category = get_object_or_404(EquipmentCategory, id=category_id)

    if request.method == "POST":
        try:
            name = request.POST.get("name", "").strip()
            description = request.POST.get("description", "").strip()
            icon = request.POST.get("icon", "").strip()

            if not name:
                messages.error(request, "Category name is required!")
                return render(
                    request,
                    "inventory_management/edit_equipment_category.html",
                    {"category": category},
                )

            # Check if name exists (excluding current category)
            if (
                EquipmentCategory.objects.filter(name__iexact=name)
                .exclude(id=category.id)
                .exists()
            ):
                messages.error(request, f'Category "{name}" already exists!')
                return render(
                    request,
                    "inventory_management/edit_equipment_category.html",
                    {"category": category},
                )

            # Update category
            category.name = name
            category.description = description
            category.icon = icon
            category.save()

            messages.success(
                request, f'Category "{category.name}" updated successfully!'
            )
            return redirect("inventory:equipment_category_list")

        except Exception as e:
            messages.error(request, f"Error updating category: {str(e)}")

    context = {
        "category": category,
    }

    return render(request, "inventory_management/edit_equipment_category.html", context)


@login_required
def delete_equipment_category(request, category_id):
    """Delete equipment category"""
    if request.user.user_type not in ["superadmin", "gymadmin"]:
        messages.error(request, "Access denied!")
        return redirect("login")

    category = get_object_or_404(EquipmentCategory, id=category_id)

    # Check if category has equipment
    equipment_count = category.equipment.count()
    if equipment_count > 0:
        messages.error(
            request,
            f'Cannot delete category "{category.name}". It has {equipment_count} equipment assigned to it!',
        )
        return redirect("inventory:equipment_category_list")

    if request.method == "POST":
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully!')
        return redirect("inventory:equipment_category_list")

    context = {
        "category": category,
        "equipment_count": equipment_count,
    }

    return render(request, "inventory_management/confirm_delete_category.html", context)
