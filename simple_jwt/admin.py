from django.contrib import admin
from .models import Staff, ClockInRecord, ClockOutRecord

admin.site.register(Staff)
admin.site.register(ClockInRecord)
admin.site.register(ClockOutRecord)

