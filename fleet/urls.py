from django.urls import path
from . import views

app_name = 'fleet'

urlpatterns = [
    # Main pages
    path('', views.landing, name='landing'),
    path('login/', views.login_page, name='login_page'),
    
    # Ambulance Module
    path('ambulance/login/', views.ambulance_login_page, name='ambulance_login_page'),
    path('ambulance/dashboard/admin/', views.ambulance_admin_dashboard, name='ambulance_admin_dashboard'),
    path('ambulance/dashboard/nectacare-head/', views.nectacare_head_dashboard, name='nectacare_head_dashboard'),
    path('ambulance/fleet/manage/', views.ambulance_manage_fleet, name='ambulance_manage_fleet'),
    path('ambulance/fleet/add/', views.ambulance_add, name='ambulance_add'),
    path('ambulance/usage/record/', views.ambulance_record_usage, name='ambulance_record_usage'),
    path('ambulance/statistics/', views.ambulance_view_statistics, name='ambulance_view_statistics'),
    
    # Dashboard routes
    path('employee/', views.employee_dashboard, name='employee_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/gm-cellmed/', views.gm_cellmed_dashboard, name='gm_cellmed_dashboard'),
    path('dashboard/gm-cellinsure/', views.gm_cellinsure_dashboard, name='gm_cellinsure_dashboard'),
    path('dashboard/gm-nectacare/', views.gm_nectacare_dashboard, name='gm_nectacare_dashboard'),
    path('dashboard/ceo/', views.ceo_dashboard, name='ceo_dashboard'),
    path('dashboard/mis/', views.mis_dashboard, name='mis_dashboard'),
    
    # GM-specific pages
    path('gm/analytics/', views.gm_analytics, name='gm_analytics'),
    path('gm/reports/', views.gm_reports, name='gm_reports'),
    path('gm/approvals/', views.gm_pending_approvals, name='gm_pending_approvals'),
    path('gm/approvals/previous/', views.gm_previous_approvals, name='gm_previous_approvals'),
    path('gm/approve/<int:request_id>/', views.gm_approve_request, name='gm_approve_request'),
    path('gm/reject/<int:request_id>/', views.gm_reject_request, name='gm_reject_request'),
    
    # Supervisor-specific pages (NEW)
    path('supervisor/approvals/', views.supervisor_pending_approvals, name='supervisor_pending_approvals'),
    path('supervisor/approve/<int:request_id>/', views.supervisor_approve_request, name='supervisor_approve_request'),
    path('supervisor/reject/<int:request_id>/', views.supervisor_reject_request, name='supervisor_reject_request'),
    
    # CEO-specific pages
    path('ceo/analytics/', views.ceo_analytics, name='ceo_analytics'),
    path('ceo/reports/', views.ceo_reports, name='ceo_reports'),
    path('ceo/approvals/', views.ceo_pending_approvals, name='ceo_pending_approvals'),
    path('ceo/approvals/previous/', views.ceo_previous_approvals, name='ceo_previous_approvals'),
    path('ceo/approve/<int:request_id>/', views.ceo_approve_request, name='ceo_approve_request'),
    path('ceo/reject/<int:request_id>/', views.ceo_reject_request, name='ceo_reject_request'),
    
    # MIS Admin functionality
    path('mis/users/manage/', views.mis_manage_users, name='mis_manage_users'),
    path('mis/users/add/', views.mis_add_user, name='mis_add_user'),
    path('mis/users/edit/<int:user_id>/', views.mis_edit_user, name='mis_edit_user'),
    path('mis/drivers/manage/', views.mis_manage_drivers, name='mis_manage_drivers'),
    path('mis/drivers/add/', views.mis_add_driver, name='mis_add_driver'),
    path('mis/drivers/delete/<int:user_id>/', views.mis_delete_driver, name='mis_delete_driver'),
    path('mis/password/reset/', views.mis_reset_password, name='mis_reset_password'),
    path('mis/audit-logs/', views.mis_audit_logs, name='mis_audit_logs'),
    
    # Admin functionality
    path('fleet-admin/vehicles/add/', views.add_vehicle, name='add_vehicle'),
    path('fleet-admin/vehicles/manage/', views.manage_vehicles, name='manage_vehicles'),
    path('fleet-admin/vehicles/edit/<int:vehicle_id>/', views.edit_vehicle, name='edit_vehicle'),
    path('fleet-admin/vehicles/details/<int:vehicle_id>/', views.vehicle_details_api, name='vehicle_details_api'),
    path('fleet-admin/vehicles/toggle-service/<int:vehicle_id>/', views.toggle_vehicle_service, name='toggle_vehicle_service'),
    path('fleet-admin/vehicles/delete/<int:vehicle_id>/', views.delete_vehicle, name='delete_vehicle'),
    path('fleet-admin/drivers/assign/', views.assign_driver, name='assign_driver'),
    path('fleet-admin/requests/manage/', views.manage_requests, name='manage_requests'),
    path('fleet-admin/requests/approve/<int:request_id>/', views.approve_request, name='approve_request'),
    path('fleet-admin/vehicle-assignments/', views.vehicle_assignments, name='vehicle_assignments'),
    path('fleet-admin/vehicle-assignments/assign/<int:request_id>/', views.assign_vehicle_to_request, name='assign_vehicle_to_request'),
    path('fleet-admin/approvals/previous/', views.admin_previous_approvals, name='admin_previous_approvals'),
    path('fleet-admin/update-mileage/', views.update_mileage, name='update_mileage'),
    
    path('fleet-admin/handovers/review/', views.review_handovers, name='review_handovers'),
    path('fleet-admin/handovers/complete/<int:request_id>/', views.complete_handover, name='complete_handover'),
    path('fleet-admin/handovers/review/<int:handover_id>/', views.review_handover_detail, name='review_handover_detail'),
    path('fleet-admin/handovers/vehicle/<int:vehicle_id>/history/', views.previous_handovers, name='previous_handovers'),
    path('fleet-admin/statistics/', views.fleet_statistics, name='fleet_statistics'),
    path('fleet-admin/statistics/export/', views.export_usage_report, name='export_usage_report'),
    path('fleet-admin/service-schedule/', views.service_schedule, name='service_schedule'),
    path('fleet-admin/service-schedule/export/', views.export_service_schedule, name='export_service_schedule'),
    path('fleet-admin/service-schedule/add/', views.add_service_record, name='add_service_record'),
    path('fleet-admin/service-schedule/vehicle/<int:vehicle_id>/history/', views.vehicle_service_history, name='vehicle_service_history'),
    
    # Employee functionality
    path('employee/request/', views.employee_request_vehicle, name='employee_request_vehicle'),
    path('employee/requests/', views.employee_my_requests, name='employee_my_requests'),
    path('employee/requests/<int:request_id>/', views.employee_request_detail, name='employee_request_detail'),
    path('employee/requests/<int:request_id>/cancel/', views.employee_cancel_request, name='employee_cancel_request'),
    path('employee/requests/<int:request_id>/edit/', views.employee_edit_request, name='employee_edit_request'),
    path('employee/vehicles/', views.employee_available_vehicles, name='employee_available_vehicles'),
    path('employee/handover/', views.employee_handover_checklist, name='employee_handover_checklist'),
    path('employee/handover/<int:request_id>/', views.employee_handover_checklist, name='employee_handover_detail'),
    
    # Ambulance Manager Routes
    path('ambulance/login/', views.ambulance_login_page, name='ambulance_login_page'),
    path('ambulance/dashboard/admin/', views.ambulance_admin_dashboard, name='ambulance_admin_dashboard'),
    path('ambulance/dashboard/nectacare-head/', views.nectacare_head_dashboard, name='nectacare_head_dashboard'),
    path('ambulance/dashboard/mis/', views.ambulance_mis_dashboard, name='ambulance_mis_dashboard'),
    path('ambulance/fleet/manage/', views.ambulance_manage_fleet, name='ambulance_manage_fleet'),
    path('ambulance/fleet/add/', views.ambulance_add, name='ambulance_add'),
    path('ambulance/driver/assign/', views.ambulance_assign_driver, name='ambulance_assign_driver'),
    path('ambulance/usage/record/', views.ambulance_record_usage, name='ambulance_record_usage'),
    path('ambulance/statistics/', views.ambulance_view_statistics, name='ambulance_view_statistics'),
    path('ambulance/mis/users/manage/', views.ambulance_mis_manage_users, name='ambulance_mis_manage_users'),
    path('ambulance/mis/users/add/', views.ambulance_mis_add_user, name='ambulance_mis_add_user'),
    path('ambulance/mis/users/<int:user_id>/reset-password/', views.ambulance_mis_reset_password, name='ambulance_mis_reset_password'),
    path('ambulance/mis/users/<int:user_id>/edit/', views.ambulance_mis_edit_user, name='ambulance_mis_edit_user'),
    path('ambulance/mis/drivers/manage/', views.ambulance_mis_manage_drivers, name='ambulance_mis_manage_drivers'),
    path('ambulance/mis/drivers/add/', views.ambulance_mis_add_driver, name='ambulance_mis_add_driver'),
    path('ambulance/mis/logs/', views.ambulance_mis_view_logs, name='ambulance_mis_view_logs'),
    
    # Ambulance Handover
    path('ambulance/handover/', views.ambulance_handover_checklist, name='ambulance_handover_checklist'),
    path('ambulance/handover/<int:trip_id>/', views.ambulance_handover_detail, name='ambulance_handover_detail'),
    
    # Ambulance Service
    path('ambulance/service/schedule/', views.ambulance_service_schedule, name='ambulance_service_schedule'),
]
