from django.db import models
from simple_jwt.models import Staff
from product.models import Product
import uuid

class Order(models.Model):
    user = models.ForeignKey(Staff, related_name='orders', on_delete=models.CASCADE)
    order_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    client_name = models.CharField(max_length=100)
    email = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=100)
    phone = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_amount = models.IntegerField()
    
    class Meta:
        ordering = ['-created_at',]
    
    def __str__(self):
        return self.client_name


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='items', on_delete=models.CASCADE)
    price = models.CharField(max_length=10)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return '%s' % self.id
