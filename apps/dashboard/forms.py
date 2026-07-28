from django import forms
from apps.store.models import Product, ProductImage
from apps.orders.models import Order
from django.forms import inlineformset_factory


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'price', 'discount_price', 'stock', 'sku', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        discount_price = cleaned_data.get('discount_price')
        if discount_price and price and discount_price >= price:
            raise forms.ValidationError({'discount_price': "Discount price must be lower than the regular price."})
        return cleaned_data


# Lets a seller add/edit multiple ProductImages on the same page as the Product form
ProductImageFormSet = inlineformset_factory(
    Product, ProductImage,
    fields=['image', 'alt_text', 'is_primary', 'order'],
    extra=1,
    can_delete=True,
)


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']
