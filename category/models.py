from django.db import models
from django.urls import reverse

# Create your models here.
class Category(models.Model):
    category_name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    description = models.TextField(max_length=300)
    cat_image = models.ImageField(upload_to = 'photos/categories', blank=True)

    def get_url(self):
        return reverse('product_category_slug',args=[self.slug])

    def __str__(self):
        return self.category_name

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

