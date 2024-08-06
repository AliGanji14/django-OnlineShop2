from django.contrib import admin

from .models import Product, Category

admin.site.register(Category)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'available', 'created']
    raw_id_fields = ('category',)
