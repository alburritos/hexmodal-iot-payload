from django.contrib import admin

from .models import Device, Payload


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("dev_eui", "latest_status", "updated_at")
    search_fields = ("dev_eui",)


@admin.register(Payload)
class PayloadAdmin(admin.ModelAdmin):
    list_display = ("device", "f_cnt", "status", "data_hex", "created_at")
    list_filter = ("status",)
    search_fields = ("device__dev_eui",)
