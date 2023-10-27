from django.contrib import admin
from .models import Order, OrderItem

# 在後台admin資料庫中建立顯示訂單的資料表
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'client_name', 'created_at', 'paid_amount')  

admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
