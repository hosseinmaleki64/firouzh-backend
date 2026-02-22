# orders/serializers.py
# این فایل رو کامل جایگزین کن
from rest_framework import serializers
from .models import Order, OrderItem
from products.models import Product          # ← این خط رو اضافه کردم (مهم!)
from products.serializers import ProductSerializer
from jdatetime import datetime as jdatetime   # برای تبدیل به تاریخ شمسی

class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    product_details = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_details', 'quantity', 'price', 'cost', 'subtotal', 'profit']
        read_only_fields = ['id', 'subtotal', 'profit', 'product_details']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    order_date_shamsi = serializers.SerializerMethodField()
    delivery_date_shamsi = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_code', 'customer_type', 'source', 'customer_name', 'customer_phone',
            'customer_address', 'items', 'order_date', 'order_date_shamsi', 'delivery_date',
            'delivery_date_shamsi', 'description', 'total_amount', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['order_code', 'total_amount', 'created_at', 'updated_at']  # تغییر داده شد: order_date حذف شد از read_only

    def get_order_date_shamsi(self, obj):
        return jdatetime.fromgregorian(datetime=obj.order_date).strftime('%Y/%m/%d %H:%M:%S')

    def get_delivery_date_shamsi(self, obj):
        if obj.delivery_date:
            return jdatetime.fromgregorian(datetime=obj.delivery_date).strftime('%Y/%m/%d %H:%M:%S')
        return None

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        validated_data['business'] = self.context['request'].user
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        order.calculate_total()
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        # آپدیت فیلدهای سفارش
        for field in ['customer_type', 'source', 'customer_name', 'customer_phone',
                      'customer_address', 'delivery_date', 'description', 'status']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                OrderItem.objects.create(order=instance, **item_data)
        instance.calculate_total()
        return instance


class MonthlySalesSerializer(serializers.Serializer):
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=0)