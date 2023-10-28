from django.shortcuts import render
from .serializers import OrderSerializer, OrderItemSerializer
from .models import Order, OrderItem
from product.models import Product
from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import APIException


# ======================  後台 API  ====================== #
# 取得所有訂單
class AllOrdersViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]


# 取得查詢的訂單
class SearchOrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    # 查詢
    @action(detail=False, methods=['GET'])
    def search(self, request):
        query_params = self.request.query_params

        search = query_params.get('search').strip('/')

        queryset = Order.objects.all()

        order_id =  queryset.filter(order_id__icontains=search)
        client_name = queryset.filter(client_name__icontains=search)
        phone = queryset.filter(phone__icontains=search)

        if order_id:
            queryset = order_id
        elif client_name:
            queryset = client_name
        elif phone:
            queryset = phone
        
        serializer = OrderSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# 刪除一筆訂單
class DeleteOrderViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    # 方法一：前端只能在接收錯誤時解析回傳值，不能提前先解析，不然會出錯
    # def destroy(self, request, pk=None):
    #     try:
    #         order = Order.objects.get(pk=pk)
    #         order.delete()
    #         return Response(status=status.HTTP_204_NO_CONTENT)
    #     except Order.DoesNotExist:
    #         return Response({"message": "找不到這筆訂單"}, status=status.HTTP_404_NOT_FOUND)

    # 方法二：前端只能在接收錯誤時解析回傳值，不能提前先解析，不然會出錯
    def destroy(self, request, pk=None):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({"message": "找不到這筆訂單"}, status=status.HTTP_404_NOT_FOUND)
        
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        




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
