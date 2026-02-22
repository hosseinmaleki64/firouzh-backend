#products/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Product)
def create_product_inventory(sender, instance, created, **kwargs):
    """وقتی محصول ساخته شد، براش انبار بساز"""
    if created:
        Inventory.objects.get_or_create(product=instance)