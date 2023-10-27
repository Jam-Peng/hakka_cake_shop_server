from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class Staff(AbstractUser):
    backend = models.BooleanField(default=False)
    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(unique=True, null=True)
    admin = models.BooleanField(default=False)
    is_delete = models.BooleanField(default=False)
    is_office_staff = models.BooleanField(default=False)
    is_vip_client = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []


class ClockInRecord(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    clock_in_time = models.DateTimeField()
    
    class Meta:
        ordering = ['-clock_in_time']
        

    def __str__(self):
        clockInTime = self.clock_in_time.astimezone(timezone.get_current_timezone()).strftime('%Y-%m-%d %H:%M:%S')
        return f"{self.staff.username} 上班時間 - {clockInTime}"


class ClockOutRecord(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    clock_out_time = models.DateTimeField()

    class Meta:
        ordering = ['-clock_out_time']

    def __str__(self):
        clockOutTime = self.clock_out_time.astimezone(timezone.get_current_timezone()).strftime('%Y-%m-%d %H:%M:%S')
        return f"{self.staff.username} 下班時間 - {clockOutTime}"

