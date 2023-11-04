from django.shortcuts import render
from .models import Staff, ClockInRecord, ClockOutRecord
from .serializers import StaffSerializer, ClockInSerializer, ClockOutSerializer, MonthlyClockInOutSerializer
from datetime import datetime, timedelta
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import InMemoryUploadedFile

# 統計每個月員工的上下班打卡記錄
from rest_framework import generics
from django.utils import timezone
from calendar import monthrange
from rest_framework.generics import CreateAPIView


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


# ======================  員工管理 API   ====================== #
# 取得全部員工資料
class StaffList(viewsets.ModelViewSet):
    queryset = Staff.objects.filter(backend=False).filter(
        is_delete=False).filter(is_office_staff=True)
    serializer_class = StaffSerializer

    # 查詢
    @action(detail=False, methods=['GET'])
    def search(self, request):
        query_params = self.request.query_params

        search = query_params.get('search')
        queryset = Staff.objects.filter(backend=False).filter(
            is_delete=False).filter(is_office_staff=True)

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
    queryset = Staff.objects.filter(backend=False).filter(is_office_staff=True)
    serializer_class = StaffSerializer
    permission_classes = [AllowAny]              # 權限配置 - 全線允許訪問
    # permission_classes = [IsAuthenticated]     # 權限配置 - 必須帶有token才可以訪問

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

        name = request.data['name']
        if name != "":
            staff.name = name
        else:
            staff.name = None

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
        staff.is_office_staff = False

        staff.save()
        return Response({"message": "已加入待刪除名單"}, status=status.HTTP_200_OK)


# 處理加入待刪除的員工
class StaffWaitSetViewSet(viewsets.ModelViewSet):
    # 取得全部待刪除員工
    queryset = Staff.objects.filter(backend=False).filter(
        is_office_staff=False).filter(is_delete=True)
    serializer_class = StaffSerializer
    permission_classes = [AllowAny]              # 權限配置 - 全線允許訪問

    def update(self, request, pk=None):
        try:
            staff = Staff.objects.get(pk=pk)
        except Staff.DoesNotExist:
            return Response({"message": "查無此員工"}, status=status.HTTP_404_NOT_FOUND)

        staff.is_delete = False
        staff.is_office_staff = True

        staff.save()
        return Response({"message": "已將員工取回"}, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        try:
            staff = Staff.objects.get(pk=pk)
        except Staff.DoesNotExist:
            return Response({"message": "查無此員工"}, status=status.HTTP_404_NOT_FOUND)

        if staff.image:
            staff.image.delete()

        staff.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# 員工上班打卡(一天只可紀錄一次)
class ClockInViewSet(viewsets.ModelViewSet):
    queryset = ClockInRecord.objects.all().order_by('-clock_in_time')
    serializer_class = ClockInSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, pk=None):
        staff = Staff.objects.get(id=pk)

        # 檢查是否有打卡記錄
        today = datetime.now().date()
        existing_clock_in = ClockInRecord.objects.filter(
            staff=staff, clock_in_time__date=today).first()

        if existing_clock_in:
            return Response({"message": "已打過上班卡"})

        clock_in_time = datetime.now()
        clockIn = ClockInRecord(staff=staff, clock_in_time=clock_in_time)
        clockIn.save()

        return Response({"message": "上班打卡成功"}, status=status.HTTP_201_CREATED)


# 員工下班打卡(重複更新紀錄)
class ClockOutViewSet(viewsets.ModelViewSet):
    queryset = ClockOutRecord.objects.all().order_by('-clock_out_time')
    serializer_class = ClockOutSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, pk=None):
        staff = Staff.objects.get(id=pk)

        clockIn = ClockInRecord.objects.filter(staff=staff).last()
        if not clockIn:
            return Response({"message": "新卡，請先打上班卡"})

        # 取得最後一次下班卡紀錄
        last_clockOutRecord = ClockOutRecord.objects.filter(
            staff=staff).first()

        # 目前時間(字串格式)
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 最後要儲存的格式
        current_datetime = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')

        # 與最後一次打卡時間做比較用 (將字串格式目前時間，轉回時間格式)
        current_strTime = datetime.now().strftime('%Y-%m-%d')
        current_date_time = datetime.strptime(current_strTime, '%Y-%m-%d')

        if last_clockOutRecord:
            # 轉換成字串
            new_time = last_clockOutRecord.clock_out_time + timedelta(hours=8)
            last_clockOutRecord_strTime = new_time.strftime('%Y-%m-%d')
            # 轉回時間格式取年月日判斷
            last_clockOutRecord_datetime = datetime.strptime(
                last_clockOutRecord_strTime, '%Y-%m-%d')

            if current_date_time != last_clockOutRecord_datetime:
                # 建立新下班打卡紀錄
                new_clockOutRecord = ClockOutRecord(
                    staff=staff, clock_out_time=current_datetime)
                new_clockOutRecord.save()
                return Response({"message": "下班打卡成功"}, status=status.HTTP_200_OK)
            else:
                # 覆蓋下班打卡記錄
                last_clockOutRecord.clock_out_time = current_datetime
                last_clockOutRecord.save()
                return Response({"message": "下班打卡成功"}, status=status.HTTP_200_OK)
        else:
            # 如果是新的下班卡就沒有前一次最後一次紀錄
            new_clockOutRecord = ClockOutRecord(
                staff=staff, clock_out_time=current_datetime)
            new_clockOutRecord.save()
            return Response({"message": "下班打卡成功"}, status=status.HTTP_200_OK)


# 更改格式合併每月每日的員工上下班打卡紀錄
class ClockInAndOutRecords(generics.ListAPIView):
    queryset = []

    def list(self, request):
        staff = Staff.objects.filter(
            backend=False, is_delete=False, is_office_staff=True)
        monthly_records = []

        for employee in staff:
            employee_records = {
                "staff": employee.username,
                "staff_id": employee.id,
                "staff_name": employee.name,
                "monthly_records": [],
            }

            for month in range(1, 13):
                records = {
                    "clock_records": [],
                }

                year = datetime.now().year             # 取得當前的年份
                num_days = monthrange(year, month)[1]  # 取得每個月的天數

                clock_in_records = ClockInRecord.objects.filter(
                    staff=employee, clock_in_time__year=year, clock_in_time__month=month)
                clock_out_records = ClockOutRecord.objects.filter(
                    staff=employee, clock_out_time__year=year, clock_out_time__month=month)

                for day in range(1, num_days + 1):
                    clock_in_data = clock_in_records.filter(
                        clock_in_time__day=day)
                    clock_out_data = clock_out_records.filter(
                        clock_out_time__day=day)

                    clock_in_time = clock_in_data[0].clock_in_time.astimezone(
                        timezone.get_current_timezone()).isoformat() if clock_in_data else None
                    clock_out_time = clock_out_data[0].clock_out_time.astimezone(
                        timezone.get_current_timezone()).isoformat() if clock_out_data else None

                    records["clock_records"].append({
                        "clock_in_time": clock_in_time,
                        "clock_out_time": clock_out_time,
                    })

                employee_records["monthly_records"].append(records)

            monthly_records.append(employee_records)

        return Response(monthly_records, status=status.HTTP_200_OK)


# 取得一個員工特定月份的上下班打卡紀錄
class OneStaffMonthClockRecords(CreateAPIView):
    serializer_class = MonthlyClockInOutSerializer

    def create(self, request, pk):
        month = request.data.get('data')

        if month is None:
            return Response({'message': '請選擇要查詢的月份'}, status=400)

        staff = Staff.objects.filter(
            backend=False, is_delete=False, is_office_staff=True, id=pk).first()

        if not staff:
            return Response({'message': '查無此員工'}, status=404)

        employee_records = {
            "staff": staff.username,
            "staff_id": staff.id,
            "staff_name": staff.name,
            "monthly_records": [],
        }

        year = timezone.now().year                  # 取得當前的年份
        num_days = monthrange(year, month)[1]       # 取得指定月份的天數

        clock_in_records = ClockInRecord.objects.filter(
            staff=staff, clock_in_time__year=year, clock_in_time__month=month)
        clock_out_records = ClockOutRecord.objects.filter(
            staff=staff, clock_out_time__year=year, clock_out_time__month=month)

        for day in range(1, num_days + 1):
            clock_in_data = clock_in_records.filter(clock_in_time__day=day)
            clock_out_data = clock_out_records.filter(clock_out_time__day=day)

            clock_in_time = clock_in_data[0].clock_in_time.astimezone(
                timezone.get_current_timezone()).isoformat() if clock_in_data else None
            clock_out_time = clock_out_data[0].clock_out_time.astimezone(
                timezone.get_current_timezone()).isoformat() if clock_out_data else None

            records = {
                "clock_in_time": clock_in_time,
                "clock_out_time": clock_out_time,
            }

            employee_records["monthly_records"].append(records)

        return Response(employee_records, status=status.HTTP_200_OK)


# ======================  會員管理 API  ====================== #
class backendClientViewSet(viewsets.ModelViewSet):
    # 取得全部會員資料
    queryset = Staff.objects.filter(
        backend=False).filter(is_delete_client=False)
    serializer_class = StaffSerializer
    permission_classes = [AllowAny]                  # 權限配置 - 全線允許訪問


# 將會員加入黑名單(將資料庫的 is_delete_client設為 True)
class DeleteClientToBlack(APIView):
    def get_client(self, pk):
        try:
            return Staff.objects.get(id=pk)
        except Staff.DoesNotExist:
            return Response({"message": "查無此會員"}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk, format=None):
        client = self.get_client(pk)
        client.is_delete_client = True

        client.save()
        return Response({"message": "已加入黑名單"}, status=status.HTTP_200_OK)


# 取得查詢的會員
class SearchClientViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer

    # 查詢
    @action(detail=False, methods=['GET'])
    def search(self, request):
        query_params = self.request.query_params

        search = query_params.get('search').strip('/')

        queryset = Staff.objects.filter(backend=False)

        username = queryset.filter(username__icontains=search)
        name = queryset.filter(name__icontains=search)
        email = queryset.filter(email__icontains=search)

        if username:
            queryset = username
        elif name:
            queryset = name
        elif email:
            queryset = email

        serializer = StaffSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# 處理加入黑名單的會員
class ClientBlackViewSet(viewsets.ModelViewSet):
    # 取得全部會員 is_delete_client= True 資料
    queryset = Staff.objects.filter(
        backend=False).filter(is_delete_client=True)
    serializer_class = StaffSerializer
    permission_classes = [AllowAny]                  # 權限配置 - 全線允許訪問

    def update(self, request, pk=None):
        try:
            client = Staff.objects.get(pk=pk)
        except Staff.DoesNotExist:
            return Response({"message": "查無此會員"}, status=status.HTTP_404_NOT_FOUND)

        client.is_delete_client = False

        client.save()
        return Response({"message": "已將會員取回"}, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        try:
            client = Staff.objects.get(pk=pk)
        except Staff.DoesNotExist:
            return Response({"message": "查無此會員"}, status=status.HTTP_404_NOT_FOUND)

        if client.image:
            client.image.delete()

        client.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ======================  前台 API  ====================== #
# 註冊和取得會員帳號
class ClientViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    permission_classes = [AllowAny]              # 權限配置 - 全線允許訪問

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
            username=username, password=password1, name=name, email=email)

        return Response({"message": "註冊成功"}, status=status.HTTP_201_CREATED)

    # 取得一個會員資料
    @action(detail=True, methods=['GET'])
    def client_profile(self, request, pk=None):
        try:
            client = Staff.objects.get(id=pk)
        except Staff.DoesNotExist:
            return Response({"message": "無此會員"}, status=status.HTTP_404_NOT_FOUND)

        # 序列化
        serializer = StaffSerializer(client)
        return Response(serializer.data, status=status.HTTP_200_OK)


# 更新會員
class ClientUpdateViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    parser_classes = (MultiPartParser, FormParser)

    def update(self, request, pk=None):
        try:
            client = Staff.objects.get(pk=pk)
        except Staff.DoesNotExist:
            return Response({"message": "無法更新"}, status=status.HTTP_404_NOT_FOUND)

        password = request.data['newPassword']
        if password:
            client.set_password(password)

        name = request.data['updatName']
        if name != "":
            client.name = name
        else:
            client.name = client.name

        if 'image' in request.data:
            new_image = request.data['image']
            if isinstance(new_image, InMemoryUploadedFile):
                if new_image.size > 0:
                    if client.image:
                        client.image.delete()
                    client.image = new_image
            else:
                client.image = client.image

        client.save()
        return Response({"message": "更新成功"}, status=status.HTTP_200_OK)
