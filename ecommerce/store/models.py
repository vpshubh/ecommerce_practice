from django.db import models
from django.conf import settings  # Add this import
from django.urls import reverse
from django.core.validators import MinValueValidator
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    image = models.ImageField(upload_to='categories/', blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, 
                              validators=[MinValueValidator(0.01)])
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, 
                                       blank=True, null=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    stock = models.PositiveIntegerField()
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.id, self.slug])

    def get_discount_percent(self):
        if self.discount_price:
            return int(100 - (self.discount_price / self.price * 100))
        return None

    class Meta:
        ordering = ['-created']
        indexes = [models.Index(fields=['id', 'slug'])]

    
    def get_recommendations(self):
        # Get products from same category
        same_category = Product.objects.filter(
            category=self.category,
            available=True
        ).exclude(id=self.id)[:4]
        
        # If not enough, get best sellers
        if same_category.count() < 4:
            best_sellers = Product.objects.filter(
                available=True
            ).annotate(
                order_count=Count('order_items')
            ).order_by('-order_count')[:4]
            return (same_category | best_sellers).distinct()[:4]
        return same_category
    
    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Changed from User
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

