from django.apps import AppConfig


class InventoryManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory_management'
    
    def ready(self):
        try:
            import inventory_management.signals
            print("✅ Inventory management signals loaded successfully")
        except ImportError as e:
            print(f"❌ Error loading signals: {e}")