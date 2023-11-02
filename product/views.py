from django.shortcuts import render
from django.db.models import Q
from .serializers import ProductSerializer
from .models import Product

from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# 使用另一種api的寫法 - 才可以使用 ＦormＤata 傳遞照片
from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.uploadedfile import InMemoryUploadedFile   # 檢查是否有新照片需要更新


@api_view(['GET'])
def getRoutes(request):
    routes = [
        '===================  Token驗證  ===================',
        {
            'GET | api/v1/',
            'POST | api/v1/token/',
            'POST | api/v1/token/refresh/',
        },
        '====================  後台使用  ====================',
        {
            'GET | api/v1/staffs/',                         # 取得全部員工
            'POST | api/v1/staff_set/',                     # 員工註冊
            'PUT | api/v1/staff_set/:id/',                  # 更新帳號
            'POST | api/v1/clock-in/:id/',                  # 上班打卡
            'PUT | api/v1/clock-out/:id/',                  # 下班打卡
            'GET | api/v1/staffs/search/?search=query',     # 搜尋員工

            'PATCH | api/v1/staff_delete/:id/',             # 將員工 is_delete設為 True
            'GET | api/v1/staff_wait_set/',                 # 取得加入待刪除的所有員工
            'PUT | api/v1/staff_wait_set/:id/',             # 取回員工
            'DELETE | api/v1/staff_delete_from_db/:id/',    # 刪除員工 (從資料庫中刪除)
        },
        {
            'GET | api/v1/back_client_set/',                # 取得所有會員 (除了系統管理員)
            'PATCH | api/v1/client_delete/:id/',            # 將會員加入黑名單
            'GET | api/v1/client_black_set',                # 取得加入黑名單的所有會員
            'PUT | api/v1/client_black_set/:id/',           # 取回會員
            'DELETE | api/v1/client_delete_from_db/:id/',   # 刪除會員 (從資料庫中刪除)
            'GET | api/v1/client/search/?search=query',     # 搜尋員工
        },
        {
            'GET | api/v1/products/',                       # 取得全部商品
            'POST | api/v1/product_set/',                   # 建立商品
            'PUT | api/v1/product_set/:id/',                # 更新商品
            'DELETE | api/v1/product_delete/:id/',          # 刪除商品
            'PATCH | api/v1/product_show/:id/',             # 更新商品是否顯示於前台
        },
        {
            'GET | api/v1/all_orders',                      # 取得所有訂單
            'DELETE | api/v1/delete_order/:id/',            # 刪除一筆訂單
            'GET | api/v1/order/search/?search=query/',     # 訂單查詢
        },
        {
            'GET | /api/v1/all_daily_order_stats/',         # 取得所有日期訂單統計(未使用)
            'GET | /api/v1/daily_order_stats/',             # 取得當日訂單統計
            'GET | /api/v1/monthly_order_stats/',           # 取得每月訂單統計
            'GET | /api/v1/yearly_order_stats/',            # 取得當年度訂單統計
            'POST | /api/v1/search_date_order_stats/',      # 搜尋日期訂單統計
        },

        '===================  前台使用  ====================',
        'POST | api/v1/client_set/',                        # 會員註冊帳號
        'GET | api/v1/front_products/',                     # 取得所有商品
        'POST | api/v1/front_order/',                       # 建立商品訂單
        'GET | api/v1/user_orders/:id/',                    # 取得一個客戶所有訂單
        'PUT | api/v1/client_update/:id/',                  # 更新會員資料
    ]
    return Response(routes)


# 取得全部產品
class ProductList(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


# 建立、更新產品
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request):
        name = request.data['name']
        category = request.data['category']
        price = request.data['price']
        description = request.data['description']
        image = request.data['image']
        Product.objects.create(
            name=name,
            category=category,
            price=price,
            description=description,
            image=image,
        )
        return Response({"message": "商品已建立"}, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"message": "找不到商品"}, status=status.HTTP_404_NOT_FOUND)

        product.name = request.data.get('name', product.name)
        product.category = request.data.get('category', product.category)
        product.price = request.data.get('price', product.price)
        product.description = request.data.get(
            'description', product.description)
        if 'image' in request.data:
            new_image = request.data['image']
            if isinstance(new_image, InMemoryUploadedFile):
                if new_image.size > 0:
                    if product.image:
                        product.image.delete()
                    product.image = new_image
            else:
                product.image = product.image

        product.save()
        return Response({"message": "商品已更新"}, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"message": "找不到商品"}, status=status.HTTP_404_NOT_FOUND)

        if product.image:
            product.image.delete()

        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# 更新 checkbox 是否顯示商品
class ProductShow(APIView):
    def get_product(self, pk):
        try:
            return Product.objects.get(id=pk)
        except Product.DoesNotExist:
            return Response({"message": "找不到商品"}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk, format=None):
        product = self.get_product(pk)

        attribute = 'complete'
        current_value = getattr(product, attribute)
        new_value = not current_value                # 切換屬性值

        setattr(product, attribute, new_value)
        product.save()

        if product.complete == True:
            return Response({"message": "商品上架"}, status=status.HTTP_200_OK)
        return Response({"message": "商品下架"}, status=status.HTTP_200_OK)


# ======================  前台 API  ====================== #
# 取得全部產品
class FrontendProductList(viewsets.ModelViewSet):
    queryset = Product.objects.filter(complete=True)
    serializer_class = ProductSerializer
