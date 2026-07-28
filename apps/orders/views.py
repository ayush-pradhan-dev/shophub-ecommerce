from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction

from .cart import CartService
from .models import Order, OrderItem
from apps.store.models import Product


def cart_detail(request):
    cart_service = CartService(request)
    items = cart_service.get_items()
    context = {
        'cart': cart_service.cart,
        'items': items,
    }
    return render(request, 'orders/cart_detail.html', context)


@require_POST
def cart_add(request, product_id):
    cart_service = CartService(request)
    quantity = int(request.POST.get('quantity', 1))

    product = get_object_or_404(Product, pk=product_id, is_active=True)
    if quantity > product.stock:
        return JsonResponse({'success': False, 'error': f'Only {product.stock} in stock.'}, status=400)

    cart_service.add(product_id, quantity)
    return JsonResponse({'success': True, 'cart_count': cart_service.cart.total_items})


@require_POST
def cart_update(request, item_id):
    cart_service = CartService(request)
    quantity = int(request.POST.get('quantity', 1))
    cart_service.update_quantity(item_id, quantity)

    items = cart_service.get_items()
    subtotal = cart_service.cart.subtotal
    return JsonResponse({
        'success': True,
        'cart_count': cart_service.cart.total_items,
        'subtotal': str(subtotal),
    })


@require_POST
def cart_remove(request, item_id):
    cart_service = CartService(request)
    cart_service.remove(item_id)
    return JsonResponse({
        'success': True,
        'cart_count': cart_service.cart.total_items,
        'subtotal': str(cart_service.cart.subtotal),
    })


def checkout(request):
    cart_service = CartService(request)
    items = list(cart_service.get_items())

    if not items:
        return redirect('orders:cart_detail')

    if request.method == 'POST':
        with transaction.atomic():
            # Re-check stock at the moment of order placement — prevents overselling
            # if stock changed between adding to cart and checking out.
            for item in items:
                if item.quantity > item.product.stock:
                    return render(request, 'orders/checkout.html', {
                        'items': items,
                        'cart': cart_service.cart,
                        'error': f"Sorry, only {item.product.stock} of {item.product.name} left in stock.",
                    })

            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                full_name=request.POST.get('full_name'),
                phone_number=request.POST.get('phone_number'),
                address_line1=request.POST.get('address_line1'),
                address_line2=request.POST.get('address_line2', ''),
                city=request.POST.get('city'),
                state=request.POST.get('state'),
                postal_code=request.POST.get('postal_code'),
                country=request.POST.get('country', 'India'),
                total_amount=cart_service.cart.subtotal,
            )

            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    price_at_purchase=item.product.current_price,
                    quantity=item.quantity,
                )
                # Decrement stock atomically
                item.product.stock -= item.quantity
                item.product.save()

            cart_service.clear()

        return redirect('orders:order_success', order_id=order.pk)

    context = {'items': items, 'cart': cart_service.cart}
    return render(request, 'orders/checkout.html', context)


def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    return render(request, 'orders/order_success.html', {'order': order})