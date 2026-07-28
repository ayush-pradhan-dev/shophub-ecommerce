from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .cart import CartService


@receiver(user_logged_in)
def merge_cart_on_login(sender, request, user, **kwargs):
    CartService.merge_guest_cart_into_user(request, user)