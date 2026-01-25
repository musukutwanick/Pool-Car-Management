from django.contrib import admin
from .models import Vehicle, Profile, CarRequest, HandoverChecklist, ServiceRecord


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('reg_number', 'model', 'vehicle_type', 'status', 'current_mileage')
    search_fields = ('reg_number', 'model', 'vehicle_type')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'subsidiary', 'is_dedicated_driver')
    search_fields = ('user__username', 'user__email')


@admin.register(CarRequest)
class CarRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'requester', 'subsidiary', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'subsidiary', 'out_of_town')
    search_fields = ('requester__username', 'purpose')


@admin.register(HandoverChecklist)
class HandoverChecklistAdmin(admin.ModelAdmin):
    list_display = ('request', 'submitted_at', 'reviewed_by', 'reviewed_at')


@admin.register(ServiceRecord)
class ServiceRecordAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'service_date', 'service_type', 'service_company', 'mileage_at_service', 'cost')
    list_filter = ('service_type', 'service_company', 'service_date')
    search_fields = ('vehicle__reg_number', 'service_company', 'description')
    date_hierarchy = 'service_date'
