#products/admin.py
from django.contrib import admin
from .models import Category, Product, Inventory

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_code', 'business', 'is_active']
    list_filter = ['is_active', 'business']
    search_fields = ['name', 'category_code']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_code', 'business', 'category', 'price', 'get_status_display']
    list_filter = ['is_active', 'unit', 'business', 'category']
    search_fields = ['name', 'product_code']
    readonly_fields = ['product_code', 'created_at', 'updated_at']
    
    def get_status_display(self, obj):
        status = obj.get_status()
        colors = {
            'green': '🟢',
            'yellow': '🟡',
            'red': '🔴',
            'نامشخص': '⚪'
        }
        return f"{colors.get(status, '')} {status}"
    get_status_display.short_description = 'وضعیت'

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'is_low_stock', 'updated_at']
    list_filter = ['product__unlimited_stock']
    search_fields = ['product__name', 'product__product_code']
