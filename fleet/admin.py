from django.contrib import admin
from .models import (
    Vehicle, Profile, CarRequest, HandoverChecklist, ServiceRecord,
    Ambulance, AmbulanceEquipment, AmbulanceServiceRecord, 
    AmbulanceUsageRecord, AmbulanceRequest
)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('reg_number', 'model', 'vehicle_type', 'status', 'current_mileage')
    search_fields = ('reg_number', 'model', 'vehicle_type')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'module', 'subsidiary', 'is_dedicated_driver')
    list_filter = ('role', 'module', 'subsidiary')
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


# ============================================
# AMBULANCE MANAGER ADMIN
# ============================================

@admin.register(Ambulance)
class AmbulanceAdmin(admin.ModelAdmin):
    list_display = ('reg_number', 'model', 'status', 'current_mileage', 'base_location', 'created_at')
    list_filter = ('status', 'base_location')
    search_fields = ('reg_number', 'model', 'chassis_number', 'engine_number')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AmbulanceEquipment)
class AmbulanceEquipmentAdmin(admin.ModelAdmin):
    list_display = ('ambulance', 'equipment_name', 'quantity', 'status', 'expiry_date', 'last_checked')
    list_filter = ('status', 'ambulance')
    search_fields = ('equipment_name', 'ambulance__reg_number')
    date_hierarchy = 'expiry_date'


@admin.register(AmbulanceServiceRecord)
class AmbulanceServiceRecordAdmin(admin.ModelAdmin):
    list_display = ('ambulance', 'service_date', 'service_type', 'service_company', 'mileage_at_service', 'cost')
    list_filter = ('service_type', 'service_company', 'service_date')
    search_fields = ('ambulance__reg_number', 'service_company', 'description')
    date_hierarchy = 'service_date'
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AmbulanceUsageRecord)
class AmbulanceUsageRecordAdmin(admin.ModelAdmin):
    list_display = ('ambulance', 'date', 'driver', 'purpose', 'start_mileage', 'end_mileage', 'distance_covered', 'fuel_cost')
    list_filter = ('ambulance', 'date', 'driver')
    search_fields = ('ambulance__reg_number', 'purpose', 'driver__username')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at', 'distance_covered')


@admin.register(AmbulanceRequest)
class AmbulanceRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'requester', 'requested_date', 'status', 'assigned_ambulance', 'approved_by')
    list_filter = ('status', 'requested_date')
    search_fields = ('requester__username', 'purpose', 'patient_name')
    date_hierarchy = 'requested_date'
    readonly_fields = ('created_at', 'updated_at')
