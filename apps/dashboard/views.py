from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.db.models import Sum, Q
from django.core.exceptions import PermissionDenied

from .permissions import seller_required, SellerRequiredMixin, SellerOwnsObjectMixin
from .forms import ProductForm, ProductImageFormSet
from apps.store.models import Product
from apps.orders.models import Order, OrderItem


@seller_required
def dashboard_home(request):
    products = Product.objects.filter(seller=request.user)

    seller_order_items = OrderItem.objects.filter(
        product__seller=request.user
    ).select_related('order', 'product')

    stats = {
        'total_products': products.count(),
        'active_products': products.filter(is_active=True).count(),
        'low_stock_count': products.filter(stock__gt=0, stock__lte=5).count(),
        'out_of_stock_count': products.filter(stock=0).count(),
        'total_orders': seller_order_items.values('order').distinct().count(),
        'pending_orders': seller_order_items.filter(order__status=Order.Status.PENDING).values('order').distinct().count(),
        'total_revenue': seller_order_items.aggregate(total=Sum('price_at_purchase'))['total'] or 0,
    }

    recent_orders = seller_order_items.order_by('-order__created_at')[:5]

    context = {'stats': stats, 'recent_orders': recent_orders}
    return render(request, 'dashboard/home.html', context)


class ProductListView(SellerRequiredMixin, SellerOwnsObjectMixin, ListView):
    model = Product
    template_name = 'dashboard/product_list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related('category').prefetch_related('images')
        search = self.request.GET.get('q', '').strip()
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(sku__icontains=search))
        return queryset.order_by('-created_at')


class ProductCreateView(SellerRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'dashboard/product_form.html'
    success_url = reverse_lazy('dashboard:product_list')

    def form_valid(self, form):
        form.instance.seller = self.request.user
        response = super().form_valid(form)

        formset = ProductImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        if formset.is_valid():
            formset.save()

        messages.success(self.request, f'"{self.object.name}" was created successfully.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ProductImageFormSet(self.request.POST, self.request.FILES)
        else:
            context['formset'] = ProductImageFormSet()
        return context


class ProductUpdateView(SellerRequiredMixin, SellerOwnsObjectMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'dashboard/product_form.html'
    success_url = reverse_lazy('dashboard:product_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        formset = ProductImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        if formset.is_valid():
            formset.save()
        messages.success(self.request, f'"{self.object.name}" was updated successfully.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ProductImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['formset'] = ProductImageFormSet(instance=self.object)
        return context


class ProductDeleteView(SellerRequiredMixin, SellerOwnsObjectMixin, DeleteView):
    model = Product
    template_name = 'dashboard/product_confirm_delete.html'
    success_url = reverse_lazy('dashboard:product_list')

    def form_valid(self, form):
        messages.success(self.request, f'"{self.object.name}" was deleted.')
        return super().form_valid(form)


@seller_required
def order_list(request):
    order_ids = OrderItem.objects.filter(
        product__seller=request.user
    ).values_list('order_id', flat=True).distinct()

    orders = Order.objects.filter(pk__in=order_ids).select_related('user').prefetch_related(
        'items'
    ).order_by('-created_at')

    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)

    context = {'orders': orders, 'status_choices': Order.Status.choices, 'current_status': status_filter}
    return render(request, 'dashboard/order_list.html', context)


@seller_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items'),
        pk=order_id,
    )

    seller_items = order.items.filter(product__seller=request.user)
    if not seller_items.exists():
        raise PermissionDenied("You don't have any items in this order.")

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.Status.choices):
            order.status = new_status
            order.save()
            messages.success(request, f'Order status updated to {order.get_status_display()}.')
            return redirect('dashboard:order_detail', order_id=order.pk)

    context = {'order': order, 'seller_items': seller_items}
    return render(request, 'dashboard/order_detail.html', context)