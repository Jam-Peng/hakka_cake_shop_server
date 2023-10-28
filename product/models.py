from django.db import models


class Product(models.Model):
    category = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    price = models.CharField(max_length=10)
    description = models.TextField(null=True, blank=True)
    complete = models.BooleanField(default=False)
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering=['created']

    def __str__(self):
        return str(self.name)
