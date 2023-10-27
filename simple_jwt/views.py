from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Staff, ClockInRecord, ClockOutRecord
from .serializers import StaffSerializer, ClockInSerializer, ClockOutSerializer
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.decorators import action
from datetime import datetime, timedelta, time

# Simple JWT 
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['username'] = user.username
        token['admin'] = user.admin
        token['name'] = user.name
        token['is_office_staff'] = user.is_office_staff
        token['is_vip_client'] = user.is_vip_client

        return token

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


# 取得全部員工資料
class StaffList(viewsets.ModelViewSet):
    queryset = Staff.objects.filter(is_delete=False).filter(is_office_staff=True)
    serializer_class = StaffSerializer

    # 查詢
    @action(detail=False, methods=['GET'])
    def search(self, request):
        query_params = self.request.query_params

        search = query_params.get('search')
        queryset = Staff.objects.filter(is_delete=False).filter(backend=False)

        email = queryset.filter(email__icontains=search)
        username = queryset.filter(username__icontains=search)
        name = queryset.filter(name__icontains=search)

        if email:
            queryset = email
        elif username:
            queryset = username
        elif name:
            queryset = name

        serializer = StaffSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# 註冊、更新員工帳號
class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.filter(is_staff=True)
    serializer_class = StaffSerializer
    permission_classes = [AllowAny]              # 權限配置 - 全線允許訪問
    # permission_classes = [IsAuthenticated]     # 權限配置 - 必須登入才可以訪問
    
    def create(self, request):
        username = request.data['username']
        password1 = request.data['password1']
        name = request.data['name']
        if name == "":
            name = None
        email = request.data['email']

        # 根據信箱檢查是否有相同的帳號
        if get_user_model().objects.filter(email=email).exists():
            return Response({"message": "帳號已註冊"}, status=status.HTTP_400_BAD_REQUEST)

        # 建立帳號
        user = get_user_model().objects.create_user(
                username=username, password=password1, name=name, email=email, is_office_staff=True)

        return Response({"message": "註冊成功"}, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        try:
            staff = Staff.objects.get(pk=pk)
        except Staff.DoesNotExist:
            return Response({"message": "無法更新"}, status=status.HTTP_404_NOT_FOUND)
        
        staff.username = request.data['username']
        password = request.data['password1']
        if password:
            staff.set_password(password)

        name =  request.data['name']
        if name != "":
            staff.name = name
        else:
            staff.name =  None

        staff.email = request.data['email']
        
        staff.save()
        return Response({"message": "帳號已更新"}, status=status.HTTP_200_OK)


# 刪除員工(將資料庫員工的 is_delete設為 True)
class DeleteStaff(APIView):
    def get_staff(self, pk):
        try:
            return Staff.objects.get(id=pk)
        except Staff.DoesNotExist:
            return Response({"message": "查無此員工"}, status=status.HTTP_404_NOT_FOUND)
        
    def patch(self, request, pk, format=None):
            staff = self.get_staff(pk)
            staff.is_delete = True

            staff.save()
            return Response({"message" : "已刪除員工"}, status=status.HTTP_200_OK)


# 員工上班打卡(只會紀錄一次)
class ClockInViewSet(viewsets.ModelViewSet):
    queryset = ClockInRecord.objects.all().order_by('-clock_in_time')
    serializer_class = ClockInSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, pk=None):
        staff = Staff.objects.get(id=pk)

        # 檢查是否有打卡記錄
        today = datetime.now().date()
        existing_clock_in = ClockInRecord.objects.filter(staff=staff, clock_in_time__date=today).first()

        if existing_clock_in:
            return Response({"message": "已打過上班卡"})

        clock_in_time = datetime.now()
        clockIn = ClockInRecord(staff=staff, clock_in_time=clock_in_time)
        clockIn.save()

        return Response({"message": "上班打卡成功"}, status=status.HTTP_201_CREATED)


# 員工下班打卡(可紀錄最新的打卡)
class ClockOutViewSet(viewsets.ModelViewSet):
    queryset = ClockOutRecord.objects.all().order_by('-clock_out_time')
    serializer_class = ClockOutSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, pk=None):
        staff = Staff.objects.get(id=pk)

        clockIn = ClockInRecord.objects.filter(staff=staff).last()
        if not clockIn:
            return Response({"message": "尚未打上班卡，請先打上班卡"})

        # 取得舊的下班卡紀錄
        clockOutRecord = ClockOutRecord.objects.filter(staff=staff).last()

        # 目前時間(字串格式)
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 設定午夜 00:00(字串格式)
        current_year = datetime.now().year
        midnight = time(0, 0).strftime(f'{current_year}-%m-%d %H:%M:%S')

        # 轉回相同時間格式做比較
        current_datetime = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
        midnight_datetime = datetime.strptime(midnight, '%Y-%m-%d %H:%M:%S')

        if not clockOutRecord or current_datetime >= midnight_datetime:
            if not clockOutRecord:
                # 建立下班卡時間
                clockOutRecord = ClockOutRecord(staff=staff, clock_out_time=current_datetime)
            else:
                # (覆盖)下班卡時間
                clockOutRecord.clock_out_time = current_datetime
            clockOutRecord.save()

        return Response({"message": "下班打卡成功"}, status=status.HTTP_200_OK)



