from django.contrib import admin
from .models import Order, OrderItem

# 在後台admin資料庫中建立顯示訂單的資料表
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'client_name', 'created_at', 'paid_amount')  

class OrderItemAdmin(admin.ModelAdmin):
    # 增加顯示帳號
    def user_username(self, obj):
        return obj.order.user.username  

    user_username.short_description = '帳號'

    list_display = ('user_username', 'order', 'product', 'price', 'quantity')

    def __str__(self):
        return f"{self.order.user.username} ({self.order.client_name})"

admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
