"""
Signal handlers for Pool Car Management System.
Triggers email notifications based on model changes.
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import CarRequest
from .email_notifications import (
    notify_supervisor_new_request,
    notify_gm_new_request,
    notify_ceo_escalation,
    notify_admin_approved_request,
    notify_employee_approved,
    notify_employee_vehicle_assigned
)
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=CarRequest)
def car_request_pre_save(sender, instance, **kwargs):
    """
    Store old values before save to detect changes.
    """
    if instance.pk:
        try:
            old = CarRequest.objects.get(pk=instance.pk)
            instance._old_supervisor_approved_by = old.supervisor_approved_by
            instance._old_gm_approved_by = old.gm_approved_by
            instance._old_ceo_approved_by = old.ceo_approved_by
            instance._old_approver1 = old.approver1
            instance._old_approver2 = old.approver2
            instance._old_status = old.status
            instance._old_assigned_vehicle = old.assigned_vehicle
        except CarRequest.DoesNotExist:
            instance._old_supervisor_approved_by = None
            instance._old_gm_approved_by = None
            instance._old_ceo_approved_by = None
            instance._old_approver1 = None
            instance._old_approver2 = None
            instance._old_status = None
            instance._old_assigned_vehicle = None
    else:
        instance._old_supervisor_approved_by = None
        instance._old_gm_approved_by = None
        instance._old_ceo_approved_by = None
        instance._old_approver1 = None
        instance._old_approver2 = None
        instance._old_status = None
        instance._old_assigned_vehicle = None


@receiver(post_save, sender=CarRequest)
def car_request_post_save(sender, instance, created, **kwargs):
    """
    Send email notifications based on request state changes.
    
    Approval Flow:
    - General Employees: Requester → Supervisor → GM → Admin → Requester (vehicle assigned)
    - Managers: Requester → CEO → Admin → Manager (vehicle assigned)
    
    Triggers:
    1. New request created:
       - General Employee → notify Supervisor
       - Manager → notify CEO
    2. Supervisor approves → notify GM
    3. GM approves → notify Admin ONLY (no employee notification yet)
    4. CEO approves → notify Admin ONLY (no employee/manager notification yet)
    5. Admin assigns vehicle → notify Requester (employee or manager)
    """
    
    # 1. New request submitted
    if created and instance.status == 'pending':
        requester_type = instance.requester_employee_type
        
        if requester_type == 'MANAGER':
            # Manager request goes directly to CEO
            logger.info(f"New manager request #{instance.id} created, notifying CEO")
            notify_ceo_escalation(instance)
        else:
            # General employee request goes to Supervisor first
            logger.info(f"New employee request #{instance.id} created, notifying Supervisor")
            notify_supervisor_new_request(instance)
        return
    
    # Get old values
    old_supervisor_approved = getattr(instance, '_old_supervisor_approved_by', None)
    old_gm_approved = getattr(instance, '_old_gm_approved_by', None)
    old_ceo_approved = getattr(instance, '_old_ceo_approved_by', None)
    old_status = getattr(instance, '_old_status', None)
    old_assigned_vehicle = getattr(instance, '_old_assigned_vehicle', None)
    
    # 2. Supervisor approved → notify GM (General Employees only)
    if (instance.supervisor_approved_by and 
        instance.supervisor_approved_by != old_supervisor_approved and 
        instance.status == 'pending'):
        logger.info(f"Request #{instance.id} approved by Supervisor, notifying GM")
        notify_gm_new_request(instance)
    
    # 3. GM approved → notify Admin ONLY (General Employees)
    if (instance.gm_approved_by and 
        instance.gm_approved_by != old_gm_approved and 
        instance.requester_employee_type == 'GENERAL_EMPLOYEE'):
        logger.info(f"Request #{instance.id} approved by GM, notifying admin")
        # Auto-transition to approved status if both supervisor and GM approved
        if instance.supervisor_approved_by and instance.status == 'pending':
            instance.status = 'approved'
            instance.save(update_fields=['status'])
    
    # 4. CEO approved → notify Admin ONLY (Managers)
    if (instance.ceo_approved_by and 
        instance.ceo_approved_by != old_ceo_approved and 
        instance.requester_employee_type == 'MANAGER'):
        logger.info(f"Request #{instance.id} approved by CEO, notifying admin")
        # Auto-transition to approved status
        if instance.status == 'pending':
            instance.status = 'approved'
            instance.save(update_fields=['status'])
    
    # 5. Request becomes approved → notify admin ONLY (no employee notification)
    if instance.status == 'approved' and old_status != 'approved':
        logger.info(f"Request #{instance.id} fully approved, notifying admin")
        notify_admin_approved_request(instance)
    
    # 6. Vehicle assigned → notify requester (employee or manager)
    if (instance.assigned_vehicle and 
        instance.assigned_vehicle != old_assigned_vehicle and 
        instance.status == 'assigned'):
        logger.info(f"Vehicle assigned to request #{instance.id}, notifying requester")
        notify_employee_vehicle_assigned(instance)
