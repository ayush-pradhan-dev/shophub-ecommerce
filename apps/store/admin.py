from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    """Allows uploading/managing multiple images directly on the Product edit page."""
    model = ProductImage
    extra = 1
    fields = ('image', 'preview', 'alt_text', 'is_primary', 'order')
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 80px; border-radius: 4px;" />', obj.image.url)
        return "—"
    preview.short_description = "Preview"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_subcategory_display', 'is_active', 'product_count')
    list_filter = ('is_active', 'parent')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('parent__name', 'name')

    def is_subcategory_display(self, obj):
        return "Subcategory" if obj.parent else "Top-level"
    is_subcategory_display.short_description = "Type"

    def get_queryset(self, request):
        # Prevent N+1 queries when rendering 'parent' and product counts in the list view
        return super().get_queryset(request).select_related('parent').prefetch_related('products')

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "Products"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'seller', 'category', 'price', 'discount_price',
        'stock_status', 'is_active', 'created_at',
    )
    list_filter = ('is_active', 'category', 'created_at')
    search_fields = ('name', 'sku', 'seller__username', 'seller__store_name')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('seller', 'category')   # perf: avoids N+1 on list view FK columns

    fieldsets = (
        ('Basic Info', {
            'fields': ('seller', 'category', 'name', 'slug', 'sku', 'description')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'discount_price', 'stock')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        # Critical perf optimization: without this, listing 50 products triggers
        # 50 extra queries (1 per row) just to fetch seller/category names.
        return super().get_queryset(request).select_related('seller', 'category')

    def stock_status(self, obj):
        if obj.stock == 0:
            color, label = 'red', 'Out of Stock'
        elif obj.is_low_stock:
            color, label = 'orange', f'Low ({obj.stock})'
        else:
            color, label = 'green', f'In Stock ({obj.stock})'
        return format_html('<span style="color: {};">●</span> {}', color, label)
    stock_status.short_description = "Stock"
