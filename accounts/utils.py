import random
from .models import Business

def generate_business_code():
    prefix = "FZ"
    while True:
        number = random.randint(100000, 999999)
        code = f"{prefix}-{number}"
        if not Business.objects.filter(business_code=code).exists():
            return code