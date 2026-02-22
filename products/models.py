# products/models.py
from django.db import models
from django.utils import timezone
from accounts.models import Business  # تغییر از BusinessAccount به Business
import random

class Category(models.Model):
    category_code = models.IntegerField()
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='categories')  # درست: ForeignKey به Business (custom user)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['business', 'category_code']
        ordering = ['category_code']

    def __str__(self):
        return f"{self.name} ({self.category_code})"

class Product(models.Model):
    UNIT_CHOICES = [
        ("number", "عدد"),
        ("kg", "کیلوگرم"),
        ("liter", "لیتر"),
        ("meter", "متر"),
        ("box", "کارتن"),
        ("pack", "بسته"),
    ]

    DEFAULT_CATEGORY_CODE = 10

    # === تنظیمات ثابت حاشیه سود (در بک‌اند - غیرقابل تغییر از فرانت) ===
    TARGET_MARGIN_PERCENT = 55      # حاشیه سود هدف (همیشه ۵۵٪)
    MIN_MARGIN_PERCENT = 10         # حداقل حاشیه برای وضعیت زرد

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='products')  # درست: ForeignKey به Business
    name = models.CharField(max_length=100)
    product_code = models.CharField(max_length=5)
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    is_active = models.BooleanField(default=True)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default="number")
    cost = models.DecimalField(max_digits=12, decimal_places=0)
    price = models.DecimalField(max_digits=12, decimal_places=0)
    description = models.TextField(blank=True, null=True)
    unlimited_stock = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['business', 'product_code']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.product_code})"

    def save(self, *args, **kwargs):
        if not self.product_code:
            self.product_code = self.generate_product_code()
        
        if not self.category:
            self.category = self.get_or_create_default_category()
        
        super().save(*args, **kwargs)

    def generate_product_code(self):
        """تولید کد ۵ رقمی یکتا برای هر بیزنس"""
        while True:
            code = str(random.randint(10000, 99999))
            if not Product.objects.filter(business=self.business, product_code=code).exists():
                return code

    def get_or_create_default_category(self):
        """دریافت یا ساخت دسته پیش‌فرض برای بیزنس"""
        default_category, created = Category.objects.get_or_create(
            business=self.business,
            category_code=self.DEFAULT_CATEGORY_CODE,
            defaults={'name': 'سایر'}
        )
        return default_category

    def get_status(self):
        """وضعیت حاشیه سود - همیشه با هدف ۵۵٪"""
        if self.cost == 0:
            return "نامشخص"
        
        margin_percent = ((self.price - self.cost) / self.price) * 100
        
        if margin_percent >= self.TARGET_MARGIN_PERCENT:
            return "green"
        elif margin_percent >= self.MIN_MARGIN_PERCENT:
            return "yellow"
        else:
            return "red"

    def calculate_new_prices(self, cost_increase_percent):
        """محاسبه قیمت جدید با حاشیه سود دقیق ۵۵٪"""
        cost_old = float(self.cost)
        price_old = float(self.price)
        
        cost_new = cost_old * (1 + cost_increase_percent / 100)
        
        target_margin = self.TARGET_MARGIN_PERCENT / 100
        recommended_price = cost_new / (1 - target_margin) if target_margin < 1 else cost_new * 2
        
        current_margin = ((price_old - cost_new) / price_old) * 100 if price_old > 0 else 0
        
        return {
            'product_code': self.product_code,
            'product_name': self.name,
            'cost_old': cost_old,
            'cost_new': round(cost_new),
            'price_old': price_old,
            'current_margin': round(current_margin, 1),
            'status': self.get_status(),
            'recommended_price': round(recommended_price),
            'should_update': current_margin < self.TARGET_MARGIN_PERCENT
        }


class Inventory(models.Model):
    product = models.OneToOneField(
        Product, 
        on_delete=models.CASCADE, 
        related_name='inventory'
    )
    quantity = models.FloatField(default=0)
    low_stock_threshold = models.FloatField(default=0, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Inventories"

    def __str__(self):
        unlimited = " (نامحدود)" if self.product.unlimited_stock else ""
        return f"{self.product.name} - {self.quantity} {self.product.unit}{unlimited}"

    def is_low_stock(self):
        if self.product.unlimited_stock:
            return False
        if self.low_stock_threshold and self.low_stock_threshold > 0:
            return self.quantity <= self.low_stock_threshold
        return False

    def add_stock(self, amount):
        if not self.product.unlimited_stock:
            self.quantity += amount
            self.save()

    def remove_stock(self, amount):
        if not self.product.unlimited_stock:
            if self.quantity >= amount:
                self.quantity -= amount
                self.save()
                return True
            return False
        return True