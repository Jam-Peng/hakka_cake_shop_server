from django.urls import path, include
from . import views
from rest_framework import routers


router = routers.DefaultRouter()
router.register('products', views.ProductList)
router.register('product_set', views.ProductViewSet)
router.register('front_products', views.FrontendProductList)    # 取得所有產品 (前台)

urlpatterns = [
    # ======================  後台 API  ====================== #
    path('', views.getRoutes),
    path('', include(router.urls)),
    path('product_delete/<int:pk>/', views.ProductViewSet.as_view({'delete': 'destroy'}), name='product-delete'),
    path('product_show/<int:pk>/', views.ProductShow.as_view()),

]
