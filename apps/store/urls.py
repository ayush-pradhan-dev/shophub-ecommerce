from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.product_list, name='home'),
    path('filter/', views.product_filter_ajax, name='product_filter_ajax'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
]