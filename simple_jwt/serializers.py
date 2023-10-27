from rest_framework import serializers
from .models import Staff, ClockInRecord, ClockOutRecord


class ClockInSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClockInRecord
        fields = ('id', 'clock_in_time')


class ClockOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClockOutRecord
        fields = ('id', 'clock_out_time')


class StaffSerializer(serializers.ModelSerializer):
    clock_in_records = ClockInSerializer(many=True, read_only=True)
    clock_out_records = ClockOutSerializer(many=True, read_only=True)
    
    class Meta:
        model = Staff
        fields = ('id', 'backend', 'name', 'username', 'email', 'password', 'admin', 'is_delete', 'is_office_staff',
                'is_vip_client', 'clock_in_records', 'clock_out_records')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        # 查詢員工上下班的打卡紀錄
        clock_in_records = ClockInRecord.objects.filter(staff=instance)
        clock_out_records = ClockOutRecord.objects.filter(staff=instance)
        
        # 序列化上下班打卡時間
        clock_in_serializer = ClockInSerializer(clock_in_records, many=True).data
        clock_out_serializer = ClockOutSerializer(clock_out_records, many=True).data
        
        data['clock_in_records'] = clock_in_serializer
        data['clock_out_records'] = clock_out_serializer

        return data
