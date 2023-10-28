from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register('front_order', views.OrderViewSet)
router.register('all_orders', views.AllOrdersViewSet)

urlpatterns = [ 
  path('', include(router.urls)),
  path('user_orders/<int:user_id>/', views.OrderViewSet.as_view({'get': 'user_orders'}), name='user_orders'),
  path('delete_order/<int:pk>/', views.DeleteOrderViewSet.as_view({'delete': 'destroy'}), name='delete_order'),
  path('order/search/', views.SearchOrderViewSet.as_view({'get': 'search'}), name='order_search'),            # 查詢訂單
]
