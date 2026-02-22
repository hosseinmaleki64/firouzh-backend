# orders/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Order
from .serializers import OrderSerializer, MonthlySalesSerializer
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()          # ← این خط رو اضافه کردم (برای router)
    serializer_class = OrderSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            # فقط سفارشات باز این بیزنس
            return Order.objects.filter(
                business=self.request.user,
                status='open'
            ).prefetch_related('items', 'items__product')
        return Order.objects.none()

    @action(detail=False, methods=['get'])
    def monthly_sales(self, request):
        """کل فروش ماهانه (۳۰ روز اخیر)"""
        now = timezone.now()
        month_start = now - timedelta(days=30)
        total = Order.objects.filter(
            business=request.user,
            created_at__gte=month_start,
            status__in=['open', 'delivered']
        ).aggregate(total_sales=Sum('total_amount'))['total_sales'] or 0
        
        return Response({'total_sales': total})

    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        """تحویل سفارش"""
        order = self.get_object()
        order.status = 'delivered'
        order.save()
        return Response({'message': 'سفارش با موفقیت تحویل شد'})
    