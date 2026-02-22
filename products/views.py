# products/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Product, Category, Inventory
from .serializers import ProductSerializer, CategorySerializer, PriceUpdateSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()  # پایه
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Category.objects.filter(business=self.request.user)  # تغییر: مستقیم به user (Business)
        return Category.objects.none()  # تغییر: برای امنیت، اگر لاگین نباشه، هیچی برنگردون

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()  # پایه
    serializer_class = ProductSerializer
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Product.objects.filter(business=self.request.user)  # تغییر: مستقیم به user (Business)
        return Product.objects.none()  # تغییر: برای امنیت

    @action(detail=True, methods=['post'])
    def calculate_price(self, request, pk=None):
        product = self.get_object()
        serializer = PriceUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            result = product.calculate_new_prices(
                serializer.validated_data['cost_increase_percent']
            )
            return Response(result)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def apply_price_update(self, request, pk=None):
        product = self.get_object()
        serializer = PriceUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            data = serializer.validated_data
            calculation = product.calculate_new_prices(data['cost_increase_percent'])
            
            if data['use_recommended']:
                new_price = calculation['recommended_price']
            else:
                new_price = data['custom_price']
            
            product.cost = calculation['cost_new']
            product.price = new_price
            product.save()
            
            return Response({
                'message': 'قیمت‌ها با موفقیت به‌روزرسانی شدند',
                'new_cost': calculation['cost_new'],
                'new_price': new_price,
                'new_margin': ((new_price - calculation['cost_new']) / new_price) * 100
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def move_to_category(self, request, pk=None):
        product = self.get_object()
        category_code = request.data.get('category_code')
        
        if not category_code:
            return Response(
                {'error': 'کد دسته را وارد کنید'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        category = get_object_or_404(
            Category, 
            category_code=category_code,
            business=self.request.user  # تغییر: فقط دسته‌های این business
        )
        
        product.category = category
        product.save()
        
        return Response({'message': 'محصول با موفقیت منتقل شد'})

    @action(detail=False, methods=['get'])
    def status_report(self, request):
        products = self.get_queryset()
        
        report = {
            'green': [],
            'yellow': [],
            'red': []
        }
        
        for product in products:
            status = product.get_status()
            report[status].append({
                'code': product.product_code,
                'name': product.name,
                'price': product.price,
                'cost': product.cost,
                'margin': ((product.price - product.cost) / product.price) * 100
            })
        
        return Response(report)