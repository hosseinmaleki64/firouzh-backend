# reports/serializers.py
from rest_framework import serializers
from orders.models import Order, OrderItem
from orders.serializers import OrderSerializer  # برای بازاستفاده

class ReportStatsSerializer(serializers.Serializer):
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=0)
    average_order_value = serializers.DecimalField(max_digits=15, decimal_places=0)
    total_orders = serializers.IntegerField()
    top_product = serializers.DictField()  # {'name': str, 'quantity': int}