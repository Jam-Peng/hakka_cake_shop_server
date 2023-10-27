from django.shortcuts import render
from .serializers import OrderSerializer, OrderItemSerializer
from .models import Order, OrderItem
from product.models import Product

from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import APIException


# ======================  前台 API  ====================== #
# 建立訂單
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request):
        current_user = request.user

        client_name = request.data['client_name']
        email = request.data['email']
        address = request.data['address']
        phone = request.data['phone']
        paid_amount = request.data['paid_amount']
        items_data = request.data['items']

        order = Order.objects.create(
            user = current_user,
            client_name = client_name,
            email = email,
            address = address,
            phone = phone,
            paid_amount = paid_amount,
        )

        # 建立訂單商品項
        for item_data in items_data:
            product_id = item_data['id']
            price = item_data['price']
            quantity = item_data['quantity']

            # 取得關聯產品
            product = Product.objects.get(pk=product_id)

            OrderItem.objects.create(
                order = order,
                product = product,
                price = price,
                quantity = quantity,
            )

        # 序列化訂單回傳前端
        order = Order.objects.get(pk=order.id)
        serializer = OrderSerializer(order)

        return Response({"message":"訂單已建立", "order": serializer.data}, status=status.HTTP_201_CREATED)

    # 取得一個使用者的訂單
    @action(detail=True, methods=['GET'])
    def user_orders(self, request, user_id=None):
        try:
            staff_id = user_id

            # 取得使用者的訂單
            orders = Order.objects.filter(user=staff_id)

            # 序列化
            serializer = OrderSerializer(orders, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            raise APIException("客戶尚未購買商品", code=status.HTTP_404_NOT_FOUND)

