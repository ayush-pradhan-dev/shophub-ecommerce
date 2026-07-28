from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_verified_seller', 'is_staff')
    list_filter = ('role', 'is_verified_seller', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Store Info', {
            'fields': ('role', 'phone_number', 'store_name', 'is_verified_seller'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role & Store Info', {
            'fields': ('role', 'email'),
        }),
    )