from .models import Cart, CartItem
from apps.store.models import Product


class CartService:
    """
    Single entry point for all cart operations. Handles the guest vs.
    authenticated distinction internally so views don't need to branch.
    """
    def __init__(self, request):
        self.request = request
        self.user = request.user if request.user.is_authenticated else None
        if self.user:
            self.cart, _ = Cart.objects.get_or_create(user=self.user)
        else:
            if not request.session.session_key:
                request.session.create()
            session_key = request.session.session_key
            self.cart, _ = Cart.objects.get_or_create(session_key=session_key)

    def add(self, product_id, quantity=1):
        product = Product.objects.get(pk=product_id, is_active=True)
        item, created = CartItem.objects.get_or_create(
            cart=self.cart, product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            item.quantity += quantity
            item.save()
        return item

    def update_quantity(self, item_id, quantity):
        item = CartItem.objects.get(pk=item_id, cart=self.cart)
        if quantity <= 0:
            item.delete()
            return None
        item.quantity = quantity
        item.save()
        return item

    def remove(self, item_id):
        CartItem.objects.filter(pk=item_id, cart=self.cart).delete()

    def clear(self):
        self.cart.items.all().delete()

    def get_items(self):
        return self.cart.items.select_related('product', 'product__category').prefetch_related('product__images')

    @staticmethod
    def merge_guest_cart_into_user(session_key, user):
        """
        Moves items from a guest's session-based cart (identified by session_key,
        captured BEFORE login() rotated the session) into the user's permanent cart.
        """
        if not session_key:
            return

        try:
            guest_cart = Cart.objects.get(session_key=session_key)
        except Cart.DoesNotExist:
            return

        user_cart, _ = Cart.objects.get_or_create(user=user)

        for guest_item in guest_cart.items.all():
            existing_item = user_cart.items.filter(product=guest_item.product).first()
            if existing_item:
                existing_item.quantity += guest_item.quantity
                existing_item.save()
            else:
                guest_item.cart = user_cart
                guest_item.save()

        guest_cart.delete()