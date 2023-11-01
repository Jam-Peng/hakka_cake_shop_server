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

# 統計訂單時使用
from django.db.models.functions import TruncDay
from django.db.models import Sum, F, ExpressionWrapper, IntegerField
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict

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

    # 寫法一：前端只能在接收錯誤時解析回傳值，不能提前先解析，不然會出錯
    # def destroy(self, request, pk=None):
    #     try:
    #         order = Order.objects.get(pk=pk)
    #         order.delete()
    #         return Response(status=status.HTTP_204_NO_CONTENT)
    #     except Order.DoesNotExist:
    #         return Response({"message": "找不到這筆訂單"}, status=status.HTTP_404_NOT_FOUND)

    # 寫法二
    def destroy(self, request, pk=None):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({"message": "找不到這筆訂單"}, status=status.HTTP_404_NOT_FOUND)
        
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# 根據“資料庫中的所有訂單”執行統計(所有訂單日期) - 取得日期、分類、商品、總數量、總金額
class AllDailyOrderStats(APIView):
    def get(self, request):
        daily_stats = (
            OrderItem.objects
            .annotate(
                order_date=TruncDay('order__created_at'),
            )
            .values('order_date', 'product__category', 'product__name')
            .annotate(
                total_quantity=Sum('quantity'),
                total_amount=ExpressionWrapper(
                    F('quantity') * F('price'),
                    output_field=IntegerField()
                )
            )
            .order_by('-order_date', 'product__category', 'product__name')
        )

        # 初始化字典格式
        stats_dict = {}

        # 組合資料格式
        for stat in daily_stats:
            order_date = stat['order_date'].strftime('%Y-%m-%dT%H:%M:%S%z')
            product_category = stat['product__category']
            product_name = stat['product__name']

            if order_date not in stats_dict:
                stats_dict[order_date] = []

            found = False
            # 檢查所有商品名稱是否有相同的，有相同只要增加數量和金額
            for item in stats_dict[order_date]:
                if item['product_category'] == product_category and item['product_name'] == product_name:
                    item['total_quantity'] += stat['total_quantity']
                    item['total_amount'] += stat['total_amount']
                    found = True
                    break

            if not found:
                stats_dict[order_date].append({
                    'product_category': product_category,
                    'product_name': product_name,
                    'total_quantity': stat['total_quantity'],
                    'total_amount': stat['total_amount']
                })

        # 轉換格式
        formatted_data = [{'order_date': key, 'items': value} for key, value in stats_dict.items()]

        # return Response({"order_stats" : formatted_data}) 組成字典格式測試
        return Response(formatted_data)


# 根據當日做統計 - 取得日期、分類、商品、總數量、總金額
class DailyOrderStats(APIView):
    def get(self, request):
        # 取得目前日期
        current_time = timezone.now()
        today = current_time.astimezone(timezone.get_current_timezone()).date() + timedelta(hours=8)

        daily_stats = (
            OrderItem.objects
            .filter(order__created_at__date=today)
            .values('order__created_at', 'product__category', 'product__name')
            .annotate(
                total_quantity=Sum('quantity'),
                total_amount=Sum(ExpressionWrapper(
                    F('quantity') * F('price'),
                    output_field=IntegerField()
                ))
            )
            .order_by('order__created_at', 'product__category', 'product__name')
        )

        # 初始化字典格式
        stats_dict = {'order_date': today.strftime('%Y-%m-%dT00:00:00+0800'), 'items': []}

        # 合併相同商品名稱的數據
        product_data = defaultdict(lambda: {'total_quantity': 0, 'total_amount': 0})
        for stat in daily_stats:
            product_category = stat['product__category']
            product_name = stat['product__name']
            total_quantity = stat['total_quantity']
            total_amount = stat['total_amount']

            # 檢查所有商品名稱是否有相同的，有相同只要增加數量和金額
            found = False
            for item in stats_dict['items']:
                if item['product_category'] == product_category and item['product_name'] == product_name:
                    item['total_quantity'] += total_quantity
                    item['total_amount'] += total_amount
                    found = True
                    break

            if not found:
                stats_dict['items'].append({
                    'product_category': product_category,
                    'product_name': product_name,
                    'total_quantity': total_quantity,
                    'total_amount': total_amount
                })

        formatted_data = [stats_dict]

        return Response(formatted_data)


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


# 統計訂單格式
# [
#     {
#         "order_date": "2023-11-01T01:10:00.194353Z",   
#         "items": [
#             {
#                 "product_category": "包子",
#                 "product__name": "小兔豆沙包(素)",
#                 "total_quantity": 2,
#                 "total_amount": 360
#             },
#             {
#                 "product_category": "粽子",
#                 "product__name": "原味鹼粽",
#                 "total_quantity": 1,
#                 "total_amount": 360
#             },
#             {
#                 "product_category": "酥餅",
#                 "product__name": "柚子奶黃酥餅",
#                 "total_quantity": 2,
#                 "total_amount": 140
#             },
#             {
#                 "product_category": "鬆糕",
#                 "product__name": "桂花鬆糕",
#                 "total_quantity": 1,
#                 "total_amount": 400
#             }
#         ]
#     }
# ]

