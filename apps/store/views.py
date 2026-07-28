from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.http import JsonResponse

from .models import Product, Category

PRODUCTS_PER_PAGE = 12


def _get_filtered_products(request):
    queryset = Product.objects.filter(is_active=True).select_related(
        'category', 'seller'
    ).prefetch_related('images')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    category_slug = request.GET.get('category', '').strip()
    if category_slug:
        queryset = queryset.filter(
            Q(category__slug=category_slug) | Q(category__parent__slug=category_slug)
        )

    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    if min_price:
        queryset = queryset.filter(price__gte=min_price)
    if max_price:
        queryset = queryset.filter(price__lte=max_price)

    sort = request.GET.get('sort', 'newest')
    sort_map = {
        'newest': '-created_at',
        'price_low': 'price',
        'price_high': '-price',
        'name': 'name',
    }
    queryset = queryset.order_by(sort_map.get(sort, '-created_at'))

    return queryset


def product_list(request):
    products = _get_filtered_products(request)

    paginator = Paginator(products, PRODUCTS_PER_PAGE)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.filter(
        parent__isnull=True, is_active=True
    ).prefetch_related('subcategories')

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': request.GET.get('category', ''),
        'current_search': request.GET.get('q', ''),
        'current_sort': request.GET.get('sort', 'newest'),
    }
    return render(request, 'store/product_list.html', context)


def product_filter_ajax(request):
    products = _get_filtered_products(request)

    paginator = Paginator(products, PRODUCTS_PER_PAGE)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    html = render_to_string('store/partials/product_grid.html', {'page_obj': page_obj}, request=request)

    return JsonResponse({
        'html': html,
        'count': paginator.count,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
    })


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category', 'seller').prefetch_related('images'),
        slug=slug,
        is_active=True,
    )

    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=product.pk).select_related('category')[:4]

    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'store/product_detail.html', context)