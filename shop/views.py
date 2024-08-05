from django.shortcuts import render, get_object_or_404
from django.views import View

from .models import Product


class ProductListView(View):
    def get(self, request):
        products = Product.objects.filter(available=True)
        return render(request, 'shop/list.html', {'products': products})


class ProductDetailView(View):
    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        return render(request, 'shop/detail.html', {'product': product})

    def post(self, request, pk):
        pass
