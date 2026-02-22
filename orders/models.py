# orders/models.py
# این فایل رو کامل جایگزین کن
from django.db import models
from accounts.models import Business
from products.models import Product
from django.utils import timezone
import random
import math
from datetime import datetime

class Order(models.Model):
    STATUS_CHOICES = [
        ('open', 'باز'),
        ('delivered', 'تحویل شده'),
        ('canceled', 'لغو شده'),
    ]

    CUSTOMER_TYPE_CHOICES = [
        ('male', 'آقا'),
        ('female', 'خانم'),
        ('legal', 'حقوقی'),
    ]

    SOURCE_CHOICES = [
        ('instagram', 'اینستاگرام'),
        ('website', 'سایت'),
        ('phone', 'تلفنی'),
        ('in_person', 'حضوری'),
        ('other', 'سایر'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='orders')
    order_code = models.CharField(max_length=20, unique=True)
    customer_type = models.CharField(max_length=10, choices=CUSTOMER_TYPE_CHOICES)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=15)
    customer_address = models.TextField()
    order_date = models.DateTimeField(default=timezone.now, blank=True, verbose_name="تاریخ ثبت سفارش")  # تغییر داده شد: default=timezone.now و blank=True
    delivery_date = models.DateTimeField(null=True, blank=True)  # میلادی، به شمسی تبدیل
    description = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_code} - {self.customer_name}"

    def save(self, *args, **kwargs):
        if not self.order_code:
            # تغییر داده شد: از order_date استفاده کن، اگر نبود timezone.now
            dt = self.order_date or timezone.now()
            self.order_code = generate_order_code(self.id or random.randint(1, 1000000), dt)
        super().save(*args, **kwargs)

    def calculate_total(self):
        total = sum(item.calculate_subtotal() for item in self.items.all())
        self.total_amount = total
        self.save()

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=1)
    price = models.DecimalField(max_digits=12, decimal_places=0)  # قیمت فروش (قابل تغییر دستی)
    cost = models.DecimalField(max_digits=12, decimal_places=0)  # هزینه (از محصول کپی می‌شه)
    subtotal = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    profit = models.DecimalField(max_digits=15, decimal_places=0, default=0)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def calculate_subtotal(self):
        self.subtotal = self.price * self.quantity
        self.profit = (self.price - self.cost) * self.quantity
        return self.subtotal

    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.product.price
        if not self.cost:
            self.cost = self.product.cost
        self.calculate_subtotal()
        super().save(*args, **kwargs)
        # کم کردن از انبار اگر unlimited_stock نباشه
        if not self.product.unlimited_stock:
            inventory = self.product.inventory
            inventory.remove_stock(self.quantity)

# تابع generate_order_code (در models یا utils)
def generate_order_code(order_id, dt):
    PREFIX = "FZ"
    day_of_year = dt.timetuple().tm_yday
    hour = dt.hour
    T = (day_of_year * 24) + hour
    MID = base36_encode(T).zfill(3).upper()
    CHECK = str((order_id + T) % 100).zfill(2)
    return f"{PREFIX}-{MID}-{CHECK}"

def base36_encode(number):
    if number == 0:
        return '0'
    chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    base36 = ''
    while number:
        number, i = divmod(number, 36)
        base36 = chars[i] + base36
    return base36