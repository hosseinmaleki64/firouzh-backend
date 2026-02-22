# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import RegexValidator

class BusinessManager(BaseUserManager):
    def create_user(self, business_code, recovery_contact, password=None, **extra_fields):
        if not business_code:
            raise ValueError('Business code is required')
        if not recovery_contact:
            raise ValueError('Recovery contact is required')

        business = self.model(
            business_code=business_code,
            recovery_contact=recovery_contact,
            **extra_fields
        )
        business.set_password(password)   # ← اینجا از متد استاندارد AbstractBaseUser استفاده می‌شه
        business.save(using=self._db)
        return business

    def create_superuser(self, business_code, recovery_contact, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(business_code, recovery_contact, password, **extra_fields)


class Business(AbstractBaseUser):
    business_code = models.CharField(max_length=20, unique=True)
    
    # فیلد استاندارد Django (به جای password_hash)
    password = models.CharField(max_length=128)
    
    recovery_contact = models.CharField(
        max_length=100,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[0-9]{10,15}$',
                message='Enter a valid phone number (10-15 digits).'
            )
        ]
    )
    status = models.CharField(
        max_length=10,
        choices=[("active", "Active"), ("suspended", "Suspended")],
        default="active"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # فیلدهای ضروری AbstractBaseUser
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = BusinessManager()

    USERNAME_FIELD = 'business_code'
    REQUIRED_FIELDS = ['recovery_contact']

    def set_password(self, raw_password):
        if len(raw_password or '') < 6:
            raise ValueError("Password must be at least 6 characters")
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.business_code

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

    @property
    def is_authenticated(self):
        return True