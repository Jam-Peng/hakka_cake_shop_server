from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

from rest_framework_simplejwt.views import (
    # TokenObtainPairView,  刪除這個換成自定義的 views.MyTokenObtainPairView
    TokenRefreshView,
)

router = DefaultRouter()
router.register('staffs', views.StaffList)
router.register('staff_set', views.StaffViewSet)
router.register('client_set', views.ClientViewSet)

urlpatterns = [
    path('token/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('', include(router.urls)),
    path('clock-in/<int:pk>/', views.ClockInViewSet.as_view({'post': 'create'}), name='clock_in'),    # 上班打卡
    path('clock-out/<int:pk>/', views.ClockOutViewSet.as_view({'put': 'update'}), name='clock_out'),  # 下班打卡
    path('staffs/search/', views.StaffList.as_view({'get': 'search'}), name='staff_search'),          # 查詢員工
    path('staff_delete/<int:pk>/', views.DeleteStaff.as_view(), name='delete_staff'),                 # 刪除員工(將is_delete設為True)

    path('client_profile/<int:pk>/', views.ClientViewSet.as_view({'get': 'client_profile'}), name='client_profile'),   # 取會員資料
    path('client_update/<int:pk>/', views.ClientUpdateViewSet.as_view({'put': 'update'}), name='client_update'),       # 更新會員資料
]
