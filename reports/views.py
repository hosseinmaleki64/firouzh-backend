# reports/views.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from orders.models import Order, OrderItem
from orders.serializers import OrderSerializer
from .serializers import ReportStatsSerializer
from django.db.models import Sum, Avg, Count, F, ExpressionWrapper
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
from django.db import models

class ReportViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = Order.objects.filter(business=self.request.user, status='delivered')
        
        # فیلتر تاریخ
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            queryset = queryset.filter(delivery_date__gte=from_date)
        if to_date:
            queryset = queryset.filter(delivery_date__lte=to_date)
        
        # جستجو بر اساس کد سفارش
        order_code = self.request.query_params.get('order_code')
        if order_code:
            queryset = queryset.filter(order_code__icontains=order_code)
        
        return queryset.order_by('-delivery_date')

    @action(detail=False, methods=['get'])
    def stats(self, request):
        queryset = self.get_queryset()  # استفاده از فیلترهای اعمال‌شده
        
        total_sales = queryset.aggregate(total=Sum('total_amount'))['total'] or 0
        average_order_value = queryset.aggregate(avg=Avg('total_amount'))['avg'] or 0
        total_orders = queryset.count()
        
        # پر فروش‌ترین محصول
        top_product_qs = OrderItem.objects.filter(
            order__in=queryset
        ).values('product__name').annotate(
            total_quantity=Sum('quantity')
        ).order_by('-total_quantity').first()
        
        top_product = {
            'name': top_product_qs['product__name'] if top_product_qs else None,
            'quantity': top_product_qs['total_quantity'] if top_product_qs else 0
        }
        
        data = {
            'total_sales': total_sales,
            'average_order_value': average_order_value,
            'total_orders': total_orders,
            'top_product': top_product
        }
        
        serializer = ReportStatsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """همه داده‌های مورد نیاز صفحه داشبورد"""
        timeframe = request.query_params.get('timeframe', 'monthly')  # daily, weekly, monthly, yearly
        business = request.user

        # فیلتر زمانی
        now = timezone.now()
        if timeframe == 'daily':
            start_date = now - timedelta(days=7)
            truncate = TruncDate('created_at')
        elif timeframe == 'weekly':
            start_date = now - timedelta(weeks=4)
            truncate = TruncWeek('created_at')
        elif timeframe == 'yearly':
            start_date = now - timedelta(days=365*5)
            truncate = TruncYear('created_at')
        else:  # monthly
            start_date = now - timedelta(days=180)
            truncate = TruncMonth('created_at')

        queryset = Order.objects.filter(
            business=business,
            created_at__gte=start_date,
            status__in=['open', 'delivered']
        )

        # ۱. خلاصه فروش
        summary = queryset.aggregate(
            total_sales=Sum('total_amount'),
            total_orders=Count('id'),
            total_cost=Sum(
                ExpressionWrapper(
                    F('items__cost') * F('items__quantity'),
                    output_field=models.DecimalField()
                )
            )
        )
        total_profit = (summary['total_sales'] or 0) - (summary['total_cost'] or 0)
        summary['total_profit'] = total_profit  # برای سازگاری با کد قبلی

        # ۲. ۳ محصول پرفروش
        top_products = OrderItem.objects.filter(
            order__in=queryset
        ).values('product__name').annotate(
            total_qty=Sum('quantity'),
            total_revenue=Sum(ExpressionWrapper(
                F('price') * F('quantity'),
                output_field=models.DecimalField()
            ))
        ).order_by('-total_qty')[:3]

        # ۳. داده‌های نمودار (فروش و سود روزانه/هفتگی/...)
        chart_data = queryset.annotate(period=truncate).values('period').annotate(
            sales=Sum('total_amount'),
            total_cost=Sum(
                ExpressionWrapper(
                    F('items__cost') * F('items__quantity'),
                    output_field=models.DecimalField()
                )
            )
        ).annotate(
            profit=ExpressionWrapper(
                F('sales') - F('total_cost'),
                output_field=models.DecimalField()
            )
        ).order_by('period')

        labels = [item['period'].strftime('%Y-%m-%d') if hasattr(item['period'], 'strftime') else str(item['period']) for item in chart_data]
        sales = [float(item['sales'] or 0) for item in chart_data]
        profit = [float(item['profit'] or 0) for item in chart_data]

        return Response({
            'summary': {
                'total_sales': summary['total_sales'] or 0,
                'total_profit': summary['total_profit'] or 0,
                'total_orders': summary['total_orders'] or 0,
            },
            'top_products': [
                {'name': p['product__name'], 'qty': p['total_qty'], 'revenue': p['total_revenue']}
                for p in top_products
            ],
            'chart': {
                'labels': labels,
                'sales': sales,
                'profit': profit
            }
        })