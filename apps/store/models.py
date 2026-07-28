from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils import timezone


class Category(models.Model):
    """
    Self-referential category model.
    A Category with parent=None is a top-level category.
    A Category with a parent is treated as a subcategory.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='subcategories',
        null=True,
        blank=True,
        help_text="Leave blank for a top-level category."
    )
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
        # A subcategory name should be unique within its parent, not globally
        constraints = [
            models.UniqueConstraint(fields=['name', 'parent'], name='unique_category_per_parent')
        ]
        indexes = [
            models.Index(fields=['parent', 'is_active']),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name

    def clean(self):
        # Prevent a category from being its own ancestor (data integrity guard)
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError("A category cannot be its own parent.")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def is_subcategory(self):
        return self.parent_id is not None


class Product(models.Model):
    """
    Core product listing. Belongs to a Category and a seller (User with role=SELLER).
    """
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='products',
        limit_choices_to={'role': 'SELLER'},
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,   # prevent deleting a category that still has products
        related_name='products',
    )

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    description = models.TextField()

    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0.01)],
        help_text="Optional. Must be lower than the regular price."
    )

    stock = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=64, unique=True, help_text="Stock Keeping Unit — unique product code.")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['seller', 'is_active']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        if self.discount_price and self.discount_price >= self.price:
            raise ValidationError({'discount_price': "Discount price must be lower than the regular price."})

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            # Guarantee uniqueness even if two products share a name
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def current_price(self):
        """The price to actually charge — discounted if available, else regular."""
        return self.discount_price if self.discount_price else self.price

    @property
    def discount_percentage(self):
        if self.discount_price:
            return round((1 - (self.discount_price / self.price)) * 100)
        return 0

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def is_low_stock(self):
        return 0 < self.stock <= 5


def product_image_upload_path(instance, filename):
    """Organizes uploads: media/products/<product_slug>/<filename>"""
    return f"products/{instance.product.slug}/{filename}"


class ProductImage(models.Model):
    """
    Multiple images per product. One should be marked as primary
    (used as the thumbnail in listings).
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ImageField(upload_to=product_image_upload_path)
    alt_text = models.CharField(max_length=255, blank=True, help_text="Accessibility & SEO description.")
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0, help_text="Controls display order in the gallery.")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'product_images'
        ordering = ['order', 'uploaded_at']
        constraints = [
        models.UniqueConstraint(
            fields=['product'],
            condition=models.Q(is_primary=True),
            name='unique_primary_image_per_product',
        )
    ]

    def __str__(self):
        return f"Image for {self.product.name} ({'primary' if self.is_primary else 'gallery'})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Ensure only one primary image per product (enforced in code, not DB constraint,
        # since DB-level "only one True per FK group" needs a partial unique index —
        # we'll add that in Phase 6 hardening).
        if self.is_primary:
            ProductImage.objects.filter(product=self.product).exclude(pk=self.pk).update(is_primary=False)