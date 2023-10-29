from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Staff, ClockInRecord, ClockOutRecord
from .serializers import StaffSerializer, ClockInSerializer, ClockOutSerializer
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.decorators import action
from datetime import datetime, timedelta
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.uploadedfile import InMemoryUploadedFile 

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
    queryset = Staff.objects.filter(is_delete=False).filter(is_office_staff=True).filter(backend=False)
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
    queryset = Staff.objects.filter(is_office_staff=True).filter(backend=False)
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
            staff.is_office_staff = False

            staff.save()
            return Response({"message" : "已將員工加入帶刪除名單"}, status=status.HTTP_200_OK)


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
            return Response({"message": "新卡，請先打上班卡"})

        # 取得最後一次下班卡紀錄
        last_clockOutRecord = ClockOutRecord.objects.filter(staff=staff).first()

        # 轉換成字串
        # new_time = last_clockOutRecord.clock_out_time + timedelta(hours=8)
        # last_clockOutRecord_strTime = new_time.strftime('%Y-%m-%d')
        # 與目前時間比較做比較用 (轉回時間格式取日期)
        # last_clockOutRecord_datetime = datetime.strptime(last_clockOutRecord_strTime , '%Y-%m-%d')


        # 目前時間(字串格式)
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 最後要儲存的格式
        current_datetime = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')

        # 與最後一次打卡時間做比較用 (將字串格式目前時間，轉回時間格式)
        current_strTime = datetime.now().strftime('%Y-%m-%d')
        current_date_time = datetime.strptime(current_strTime, '%Y-%m-%d')
        
        if last_clockOutRecord:
            new_time = last_clockOutRecord.clock_out_time + timedelta(hours=8)
            last_clockOutRecord_strTime = new_time.strftime('%Y-%m-%d')
            last_clockOutRecord_datetime = datetime.strptime(last_clockOutRecord_strTime , '%Y-%m-%d')

            if current_date_time != last_clockOutRecord_datetime:
                # 建立新下班打卡紀錄
                new_clockOutRecord = ClockOutRecord(staff=staff, clock_out_time=current_datetime)
                new_clockOutRecord.save()
                return Response({"message": "下班打卡成功"}, status=status.HTTP_200_OK)
            else:
                # 覆蓋下班打卡記錄
                last_clockOutRecord.clock_out_time = current_datetime
                last_clockOutRecord.save()
                return Response({"message": "下班打卡成功"}, status=status.HTTP_200_OK)
        else:
            # 如果是新的下班卡就沒有前一次最後一次紀錄
            new_clockOutRecord = ClockOutRecord(staff=staff, clock_out_time=current_datetime)
            new_clockOutRecord.save()
            return Response({"message": "下班打卡成功"}, status=status.HTTP_200_OK)


# 處理會員管理
class backendClientViewSet(viewsets.ModelViewSet):
    # 取得全部會員資料
    queryset = Staff.objects.filter(backend=False).filter(is_delete_client=False)
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
            return Response({"message" : "已將會員加入黑名單"}, status=status.HTTP_200_OK)


# 取得查詢的會員
class SearchClientViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer

    # 查詢
    @action(detail=False, methods=['GET'])
    def search(self, request):
        query_params = self.request.query_params

        search = query_params.get('search').strip('/')

        queryset = Staff.objects.all()

        username =  queryset.filter(username__icontains=search)
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

        name =  request.data['updatName']
        if name != "":
            client.name = name
        else:
            client.name =  client.name

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

