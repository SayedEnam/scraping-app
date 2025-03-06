from django.contrib import admin
from .models import Product


admin.site.register(Product)


# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ('title', 'description', 'price', 'image_url', 'scraped_at')
