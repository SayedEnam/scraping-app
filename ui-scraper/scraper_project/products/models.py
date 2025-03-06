from django.db import models

class Product(models.Model):
    category = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    image_url = models.URLField(max_length=500)
    price = models.CharField(max_length=50)
    description = models.TextField()
    product_link = models.URLField(max_length=500)

    def __str__(self):
        return self.title
