from django.contrib.auth.models import AbstractUser

from django.db import models

class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    # Add these to resolve the reverse accessor clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',  # Changed from default 'user_set'
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',  # Changed from default 'user_set'
        related_query_name='user',
    )
    
    def __str__(self):
        return self.username
    
LOW_STOCK_THRESHOLD = 5

class Product(models.Model):
    # ... existing fields ...

    @property
    def is_low_stock(self):
        return self.stock <= self.LOW_STOCK_THRESHOLD

    @property
    def stock_status(self):
        if self.stock == 0:
            return 'out-of-stock'
        elif self.is_low_stock:
            return 'low-stock'
        return 'in-stock'