# products/serializers.py
from rest_framework import serializers
from .models import Category, Product, Inventory

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'category_code', 'name', 'is_active']
        read_only_fields = ['category_code']

    def create(self, validated_data):
        # کد دسته بعدی رو پیدا کن
        business = self.context['request'].user  # تغییر: مستقیم user (که Business هست)
        last_category = Category.objects.filter(business=business).order_by('category_code').last()
        next_code = (last_category.category_code + 1) if last_category else 11
        
        validated_data['business'] = business
        validated_data['category_code'] = next_code
        return super().create(validated_data)

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    inventory_quantity = serializers.FloatField(source='inventory.quantity', read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'product_code', 'name', 'category', 'category_name',
            'unit', 'cost', 'price', 'description', 'unlimited_stock',
            'inventory_quantity', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['product_code', 'created_at', 'updated_at']

    def get_status(self, obj):
        return obj.get_status()

    def create(self, validated_data):
        validated_data['business'] = self.context['request'].user  # تغییر: مستقیم user
        return super().create(validated_data)

class PriceUpdateSerializer(serializers.Serializer):
    cost_increase_percent = serializers.FloatField(min_value=0, max_value=1000)
    use_recommended = serializers.BooleanField(default=True)
    custom_price = serializers.DecimalField(max_digits=12, decimal_places=0, required=False, allow_null=True)

    def validate(self, data):
        if not data['use_recommended'] and not data.get('custom_price'):
            raise serializers.ValidationError("اگر از قیمت پیشنهادی استفاده نمی‌کنید، قیمت جدید را وارد کنید")
        return data