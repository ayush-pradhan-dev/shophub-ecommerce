from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class User(AbstractUser):
    """
    Custom User model extending AbstractUser.
    Adds role-based access control (RBAC) foundation for the platform.
    """

    class Role(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Customer'
        SELLER = 'SELLER', 'Seller'
        ADMIN = 'ADMIN', 'Admin'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CUSTOMER,
        db_index=True,
    )

    email = models.EmailField(unique=True)

    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex], max_length=17, blank=True, null=True
    )

    store_name = models.CharField(max_length=255, blank=True, null=True)
    is_verified_seller = models.BooleanField(
        default=False,
        help_text="Sellers must be verified by an Admin before they can list products."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['role', 'is_verified_seller']),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER

    @property
    def is_seller(self):
        return self.role == self.Role.SELLER

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def can_sell(self):
        return self.is_seller and self.is_verified_seller