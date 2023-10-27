from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register('front_order', views.OrderViewSet)

urlpatterns = [ 
  path('', include(router.urls)),
  path('user_orders/<int:user_id>/', views.OrderViewSet.as_view({'get': 'user_orders'}), name='user_orders'),
]
