from rest_framework import serializers
from .models import Staff, ClockInRecord, ClockOutRecord
from order.serializers import OrderSerializer
from django.utils import timezone


class ClockInSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClockInRecord
        fields = ('id', 'clock_in_time')


class ClockOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClockOutRecord
        fields = ('id', 'clock_out_time')


# 處理上下班打卡紀錄合併統計
class MonthlyClockInOutSerializer(serializers.Serializer):
    staff = serializers.CharField()
    monthly_records = serializers.DictField(child=serializers.DictField(
        child=serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")
    ))

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # 調整時間加 8小時
        for staff, records in data.items():
            for month, record in records['monthly_records'].items():
                for key, value in record.items():
                    if key == 'clock_in_records' or key == 'clock_out_records':
                        for entry in value:
                            if 'clock_in_time' in entry:
                                entry['clock_in_time'] = entry['clock_in_time'].astimezone(
                                    timezone.get_current_timezone()) + timezone.timedelta(hours=8)
                            if 'clock_out_time' in entry:
                                entry['clock_out_time'] = entry['clock_out_time'].astimezone(
                                    timezone.get_current_timezone()) + timezone.timedelta(hours=8)

        return data


# class StaffSerializer(serializers.ModelSerializer):
class StaffSerializer(serializers.HyperlinkedModelSerializer):
    clock_in_records = ClockInSerializer(many=True, read_only=True)
    clock_out_records = ClockOutSerializer(many=True, read_only=True)

    image = serializers.ImageField(
        max_length=None, allow_empty_file=False, allow_null=False, use_url=True, required=False)

    orders = OrderSerializer(many=True, read_only=True)  # 引用訂單序列化，加到每個 staff裡

    class Meta:
        model = Staff
        fields = ('id', 'backend', 'name', 'username', 'email', 'password', 'admin', 'is_delete', 'is_office_staff',
                  'is_vip_client', 'clock_in_records', 'clock_out_records', 'image', 'orders', 'is_delete_client')

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # 查詢員工上下班的打卡紀錄
        clock_in_records = ClockInRecord.objects.filter(staff=instance)
        clock_out_records = ClockOutRecord.objects.filter(staff=instance)

        # 序列化上下班打卡時間
        clock_in_serializer = ClockInSerializer(
            clock_in_records, many=True).data
        clock_out_serializer = ClockOutSerializer(
            clock_out_records, many=True).data

        data['clock_in_records'] = clock_in_serializer
        data['clock_out_records'] = clock_out_serializer

        return data
