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
router.register('staff_wait_set', views.StaffWaitSetViewSet)

router.register('client_set', views.ClientViewSet)
router.register('back_client_set', views.backendClientViewSet)
router.register('client_black_set', views.ClientBlackViewSet)

urlpatterns = [
    path('token/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('', include(router.urls)),
    path('clock-in/<int:pk>/', views.ClockInViewSet.as_view({'post': 'create'}),
         name='clock_in'),                                                               # 上班打卡
    path('clock-out/<int:pk>/', views.ClockOutViewSet.as_view({'put': 'update'}),
         name='clock_out'),                                                              # 下班打卡
    path('staff_clock_in_out_records/', views.ClockInAndOutRecords.as_view(),
         name='clock-in-out-records'),                                                   # 當年每月上下班打卡統計
    path('staff_one_month_clock_records/<int:pk>/', views.OneStaffMonthClockRecords.as_view(),
         name='staff_one_month_clock_records'),                                          # 取得一個員工特定月份打卡紀錄

    path('staffs/search/', views.StaffList.as_view({'get': 'search'}),
         name='staff_search'),                                                           # 查詢員工
    path('staff_delete/<int:pk>/', views.DeleteStaff.as_view(),
         name='delete_staff'),                                                           # 刪除員工(將is_delete設為True)
    path('staff_delete_from_db/<int:pk>/', views.StaffWaitSetViewSet.as_view({'delete': 'destroy'}),
         name='staff_delete_from_db'),                                                   # 刪除員工(從資料庫中刪除)

    path('client/search/', views.SearchClientViewSet.as_view({'get': 'search'}),
         name='client_search'),                                                          # 查詢會員
    path('client_delete/<int:pk>/', views.DeleteClientToBlack.as_view(),
         name='delete_client'),                                                          # 刪除會員(將is_delete_client設為True)
    path('client_delete_from_db/<int:pk>/', views.ClientBlackViewSet.as_view({'delete': 'destroy'}),
         name='client_delete_from_db'),                                                  # 刪除會員(從資料庫中刪除)

    # =======================  前台  ======================= #
    path('client_profile/<int:pk>/', views.ClientViewSet.as_view({'get': 'client_profile'}),
         name='client_profile'),                                                         # 取單一會員資料
    path('client_update/<int:pk>/', views.ClientUpdateViewSet.as_view({'put': 'update'}),
         name='client_update'),                                                          # 更新會員資料
]
