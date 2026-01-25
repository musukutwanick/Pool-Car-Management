"""
Email notification utilities for Pool Car Management System.
Handles all email communications for vehicle requests and assignments.
"""
from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import strip_tags
from typing import List
import logging

logger = logging.getLogger(__name__)


def send_email_notification(subject: str, html_message: str, recipients: List[str]) -> bool:
    """
    Core email sending function.
    
    Args:
        subject: Email subject line
        html_message: HTML content of the email
        recipients: List of recipient email addresses
        
    Returns:
        bool: True if email was sent successfully
    """
    if not recipients:
        logger.warning("No recipients provided for email")
        return False
    
    # Filter out empty emails
    recipients = [email.strip() for email in recipients if email and email.strip()]
    if not recipients:
        logger.warning("All recipient emails were empty")
        return False
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', getattr(settings, 'EMAIL_HOST_USER', None))
    
    if not from_email:
        logger.error("No from_email configured in settings")
        return False
    
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=recipients,
            html_message=html_message,
            fail_silently=True
        )
        logger.info(f"Email sent successfully to {', '.join(recipients)}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False


def notify_gm_new_request(car_request) -> bool:
    """
    Notify GM when supervisor approves a general employee request.
    For both local and out-of-town trips.
    
    Args:
        car_request: CarRequest instance
        
    Returns:
        bool: True if notification sent successfully
    """
    from .models import Profile
    
    # Get GM for this subsidiary
    try:
        gm_profile = Profile.objects.filter(
            role='gm',
            subsidiary=car_request.subsidiary
        ).select_related('user').first()
        
        if not gm_profile or not gm_profile.user.email:
            logger.warning(f"No GM email found for subsidiary {car_request.subsidiary}")
            return False
        
        gm = gm_profile.user
    except Exception as e:
        logger.error(f"Error finding GM: {str(e)}")
        return False
    
    requester = car_request.requester
    supervisor = car_request.supervisor_approved_by
    
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #fed41f; padding: 20px; text-align: center;">
                <h2 style="margin: 0; color: #000;">GM Approval Required - Supervisor Approved</h2>
            </div>
            <div style="background-color: #f9f9f9; padding: 20px; margin-top: 20px;">
                <p>Hello <strong>{gm.get_full_name() or gm.username}</strong>,</p>
                <p>A vehicle request has been approved by the supervisor and now requires your approval.</p>
                
                <div style="background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #fed41f;">
                    <h3 style="margin-top: 0; color: #000;">Request Details</h3>
                    <p><strong>Request ID:</strong> #{car_request.request_code or car_request.id}</p>
                    <p><strong>Requester:</strong> {requester.get_full_name() or requester.username}</p>
                    <p><strong>Supervisor Approved by:</strong> {supervisor.get_full_name() or supervisor.username if supervisor else 'N/A'}</p>
                    <p><strong>Purpose:</strong> {car_request.purpose}</p>
                    <p><strong>Destination:</strong> {car_request.location}</p>
                    <p><strong>Start:</strong> {car_request.start_time.strftime('%d %B %Y, %I:%M %p')}</p>
                    <p><strong>End:</strong> {car_request.end_time.strftime('%d %B %Y, %I:%M %p')}</p>
                    {'<p><strong>Driver Required:</strong> Yes</p>' if car_request.needs_driver else ''}
                    {'<p style=\"color: #d97706; font-weight: 600;\"><strong>Out of Town:</strong> Yes</p>' if car_request.out_of_town else '<p><strong>Local Trip</strong></p>'}
                </div>
                
                <p>Please review and approve this request in the Pool Car Management dashboard.</p>
            </div>
            <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                <p>Pool Car Management System</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    subject = f"GM Approval Required - Request #{car_request.request_code or car_request.id}"
    
    return send_email_notification(subject, html_message, [gm.email])


def notify_supervisor_new_request(car_request) -> bool:
    """
    Notify Supervisor when a general employee submits a new booking request.
    
    Args:
        car_request: CarRequest instance
        
    Returns:
        bool: True if notification sent successfully
    """
    from .models import Profile
    
    requester = car_request.requester
    
    # Get the selected supervisor from the request
    try:
        if not car_request.selected_supervisor:
            logger.warning(f"No supervisor selected for request {car_request.id}")
            return False
        
        supervisor = car_request.selected_supervisor
        
        if not supervisor.email:
            logger.warning(f"No email found for supervisor {supervisor.username}")
            return False
    except Exception as e:
        logger.error(f"Error finding supervisor: {str(e)}")
        return False
    
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #fed41f; padding: 20px; text-align: center;">
                <h2 style="margin: 0; color: #000;">New Vehicle Request - Supervisor Approval Required</h2>
            </div>
            <div style="background-color: #f9f9f9; padding: 20px; margin-top: 20px;">
                <p>Hello <strong>{supervisor.get_full_name() or supervisor.username}</strong>,</p>
                <p>A new vehicle request has been submitted by your team member and requires your approval.</p>
                
                <div style="background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #fed41f;">
                    <h3 style="margin-top: 0; color: #000;">Request Details</h3>
                    <p><strong>Request ID:</strong> #{car_request.request_code or car_request.id}</p>
                    <p><strong>Requester:</strong> {requester.get_full_name() or requester.username}</p>
                    <p><strong>Purpose:</strong> {car_request.purpose}</p>
                    <p><strong>Destination:</strong> {car_request.location}</p>
                    <p><strong>Start:</strong> {car_request.start_time.strftime('%d %B %Y, %I:%M %p')}</p>
                    <p><strong>End:</strong> {car_request.end_time.strftime('%d %B %Y, %I:%M %p')}</p>
                    {'<p><strong>Driver Required:</strong> Yes</p>' if car_request.needs_driver else ''}
                    {'<p><strong>Out of Town:</strong> Yes</p>' if car_request.out_of_town else ''}
                </div>
                
                <p>Please review and approve this request in the Pool Car Management dashboard. Once approved, it will be forwarded to the GM for final approval.</p>
            </div>
            <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                <p>Pool Car Management System</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    subject = f"Supervisor Approval Required - Request #{car_request.request_code or car_request.id}"
    
    return send_email_notification(subject, html_message, [supervisor.email])


def notify_ceo_escalation(car_request) -> bool:
    """
    Notify CEO when:
    1. A Manager submits a request (direct to CEO)
    2. GM approves a long-distance booking (legacy flow - still supported)
    
    Args:
        car_request: CarRequest instance
        
    Returns:
        bool: True if notification sent successfully
    """
    from .models import Profile
    
    # Get CEO
    try:
        ceo_profile = Profile.objects.filter(role='ceo').select_related('user').first()
        
        if not ceo_profile or not ceo_profile.user.email:
            logger.warning(f"No CEO email found for request #{car_request.id}")
            return False
        
        ceo = ceo_profile.user
    except Exception as e:
        logger.error(f"Error finding CEO: {str(e)}")
        return False
    
    requester = car_request.requester
    requester_type = car_request.requester_employee_type
    
    # Determine if this is a manager request or escalation
    is_manager_request = requester_type == 'MANAGER'
    
    if is_manager_request:
        title = "Manager Request - CEO Approval Required"
        intro = "A vehicle request has been submitted by a Manager and requires your approval."
    else:
        gm = car_request.gm_approved_by or car_request.approver1
        title = "Long Distance Request - CEO Approval Required"
        intro = f"A long-distance vehicle request has been approved by the GM and requires your final approval."
    
    approval_info = ""
    if not is_manager_request and (car_request.gm_approved_by or car_request.approver1):
        gm_approver = car_request.gm_approved_by or car_request.approver1
        approval_info = f"<p><strong>Approved by GM:</strong> {gm_approver.get_full_name() or gm_approver.username}</p>"
    
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #fed41f; padding: 20px; text-align: center;">
                <h2 style="margin: 0; color: #000;">{title}</h2>
            </div>
            <div style="background-color: #f9f9f9; padding: 20px; margin-top: 20px;">
                <p>Hello <strong>{ceo.get_full_name() or ceo.username}</strong>,</p>
                <p>{intro}</p>
                
                <div style="background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #fed41f;">
                    <h3 style="margin-top: 0; color: #000;">Request Details</h3>
                    <p><strong>Request ID:</strong> #{car_request.request_code or car_request.id}</p>
                    <p><strong>Requester:</strong> {requester.get_full_name() or requester.username}</p>
                    {'<p><strong>Requester Type:</strong> Manager</p>' if is_manager_request else ''}
                    {approval_info}
                    <p><strong>Purpose:</strong> {car_request.purpose}</p>
                    <p><strong>Destination:</strong> {car_request.location}</p>
                    <p><strong>Start:</strong> {car_request.start_time.strftime('%d %B %Y, %I:%M %p')}</p>
                    <p><strong>End:</strong> {car_request.end_time.strftime('%d %B %Y, %I:%M %p')}</p>
                    {'<p><strong>Driver Required:</strong> Yes</p>' if car_request.needs_driver else ''}
                    {'<p><strong>Out of Town:</strong> Yes</p>' if car_request.out_of_town else ''}
                </div>
                
                <p>Please review and approve this request in the Pool Car Management dashboard.</p>
            </div>
            <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                <p>Pool Car Management System</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    subject = f"CEO Approval Required - Request #{car_request.request_code or car_request.id}"
    
    return send_email_notification(subject, html_message, [ceo.email])


def notify_admin_approved_request(car_request) -> bool:
    """
    Notify admin when request is fully approved and ready for vehicle assignment.
    
    Args:
        car_request: CarRequest instance
        
    Returns:
        bool: True if notification sent successfully
    """
    from .models import Profile
    
    # Get all admins
    try:
        admin_profiles = Profile.objects.filter(role='admin').select_related('user')
        admin_emails = [p.user.email for p in admin_profiles if p.user and p.user.email]
        
        if not admin_emails:
            logger.warning(f"No admin emails found for request #{car_request.id}")
            return False
    except Exception as e:
        logger.error(f"Error finding admins: {str(e)}")
        return False
    
    requester = car_request.requester
    
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #fed41f; padding: 20px; text-align: center;">
                <h2 style="margin: 0; color: #000;">Request Approved - Vehicle Assignment Required</h2>
            </div>
            <div style="background-color: #f9f9f9; padding: 20px; margin-top: 20px;">
                <p>Hello Admin,</p>
                <p>Vehicle request has been fully approved and is ready for vehicle assignment.</p>
                
                <div style="background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #fed41f;">
                    <h3 style="margin-top: 0; color: #000;">Request Details</h3>
                    <p><strong>Request ID:</strong> #{car_request.request_code or car_request.id}</p>
                    <p><strong>Requester:</strong> {requester.get_full_name() or requester.username}</p>
                    <p><strong>Purpose:</strong> {car_request.purpose}</p>
                    <p><strong>Destination:</strong> {car_request.location}</p>
                    <p><strong>Start:</strong> {car_request.start_time.strftime('%d %B %Y, %I:%M %p')}</p>
                    <p><strong>End:</strong> {car_request.end_time.strftime('%d %B %Y, %I:%M %p')}</p>
                    {'<p><strong>Driver Required:</strong> Yes</p>' if car_request.needs_driver else ''}
                    {'<p><strong>Out of Town:</strong> Yes</p>' if car_request.out_of_town else ''}
                </div>
                
                <p>Please assign a vehicle to this request in the admin dashboard.</p>
            </div>
            <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                <p>Pool Car Management System</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    subject = f"Action Required - Assign Vehicle to Request #{car_request.request_code or car_request.id}"
    
    return send_email_notification(subject, html_message, admin_emails)


def notify_employee_approved(car_request) -> bool:
    """
    Notify employee when their request is approved.
    
    Args:
        car_request: CarRequest instance
        
    Returns:
        bool: True if notification sent successfully
    """
    requester = car_request.requester
    
    if not requester.email:
        logger.warning(f"No email for requester {requester.username}")
        return False
    
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #10b981; padding: 20px; text-align: center;">
                <h2 style="margin: 0; color: #fff;">Request Approved!</h2>
            </div>
            <div style="background-color: #f9f9f9; padding: 20px; margin-top: 20px;">
                <p>Hello <strong>{requester.get_full_name() or requester.username}</strong>,</p>
                <p>Good news! Your vehicle request has been approved.</p>
                
                <div style="background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #10b981;">
                    <h3 style="margin-top: 0; color: #000;">Request Details</h3>
                    <p><strong>Request ID:</strong> #{car_request.request_code or car_request.id}</p>
                    <p><strong>Purpose:</strong> {car_request.purpose}</p>
                    <p><strong>Destination:</strong> {car_request.location}</p>
                    <p><strong>Start:</strong> {car_request.start_time.strftime('%d %B %Y, %I:%M %p')}</p>
                    <p><strong>End:</strong> {car_request.end_time.strftime('%d %B %Y, %I:%M %p')}</p>
                </div>
                
                <p>You will receive another notification once a vehicle has been assigned to your request.</p>
            </div>
            <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                <p>Pool Car Management System</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    subject = f"Your Vehicle Request #{car_request.request_code or car_request.id} Has Been Approved"
    
    return send_email_notification(subject, html_message, [requester.email])


def notify_employee_vehicle_assigned(car_request) -> bool:
    """
    Notify employee when vehicle is assigned to their request.
    
    Args:
        car_request: CarRequest instance
        
    Returns:
        bool: True if notification sent successfully
    """
    requester = car_request.requester
    
    if not requester.email:
        logger.warning(f"No email for requester {requester.username}")
        return False
    
    if not car_request.assigned_vehicle:
        logger.warning(f"No vehicle assigned to request #{car_request.id}")
        return False
    
    vehicle = car_request.assigned_vehicle
    
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #fed41f; padding: 20px; text-align: center;">
                <h2 style="margin: 0; color: #000;">Vehicle Assigned!</h2>
            </div>
            <div style="background-color: #f9f9f9; padding: 20px; margin-top: 20px;">
                <p>Hello <strong>{requester.get_full_name() or requester.username}</strong>,</p>
                <p>A vehicle has been assigned to your request.</p>
                
                <div style="background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #fed41f;">
                    <h3 style="margin-top: 0; color: #000;">Assignment Details</h3>
                    <p><strong>Request ID:</strong> #{car_request.request_code or car_request.id}</p>
                    <p><strong>Vehicle:</strong> {vehicle.reg_number}</p>
                    <p><strong>Model:</strong> {vehicle.model or vehicle.vehicle_type}</p>
                    <p><strong>Fuel Type:</strong> {vehicle.fuel_type}</p>
                    <p><strong>Purpose:</strong> {car_request.purpose}</p>
                    <p><strong>Destination:</strong> {car_request.location}</p>
                    <p><strong>Start:</strong> {car_request.start_time.strftime('%d %B %Y, %I:%M %p')}</p>
                    <p><strong>End:</strong> {car_request.end_time.strftime('%d %B %Y, %I:%M %p')}</p>
                </div>
                
                <p>Please collect the vehicle at the scheduled time and complete the handover checklist.</p>
            </div>
            <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                <p>Pool Car Management System</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    subject = f"Vehicle {vehicle.reg_number} Assigned to Your Request #{car_request.request_code or car_request.id}"
    
    return send_email_notification(subject, html_message, [requester.email])


def notify_rejection(car_request, rejected_by, reason: str) -> bool:
    """
    Notify employee that their vehicle request was rejected.
    
    Args:
        car_request: CarRequest instance that was rejected
        rejected_by: User who rejected the request
        reason: Reason for rejection
        
    Returns:
        bool: True if email was sent successfully
    """
    requester = car_request.requester
    if not requester.email:
        logger.warning(f"Requester {requester.username} has no email address")
        return False
    
    rejector_name = rejected_by.get_full_name() or rejected_by.username
    requester_name = requester.get_full_name() or requester.username
    request_code = car_request.request_code or car_request.id
    
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #ef4444, #dc2626); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-radius: 0 0 10px 10px; }}
            .detail-box {{ background: #f9fafb; padding: 15px; border-left: 4px solid #ef4444; margin: 20px 0; border-radius: 4px; }}
            .detail-row {{ margin: 10px 0; }}
            .label {{ font-weight: 600; color: #374151; }}
            .value {{ color: #111827; }}
            .reason-box {{ background: #fef2f2; border: 1px solid #fecaca; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 12px; }}
            .btn {{ display: inline-block; padding: 12px 24px; background: #3b82f6; color: white; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0;">❌ Request Rejected</h1>
            </div>
            <div class="content">
                <p>Dear {requester_name},</p>
                
                <p>Your vehicle request <strong>#{request_code}</strong> has been rejected.</p>
                
                <div class="detail-box">
                    <div class="detail-row">
                        <span class="label">Request ID:</span>
                        <span class="value">#{request_code}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Purpose:</span>
                        <span class="value">{car_request.purpose}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Destination:</span>
                        <span class="value">{car_request.location}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Date:</span>
                        <span class="value">{car_request.start_time.strftime('%B %d, %Y at %I:%M %p')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Rejected by:</span>
                        <span class="value">{rejector_name}</span>
                    </div>
                </div>
                
                <div class="reason-box">
                    <strong style="color: #991b1b;">Reason for Rejection:</strong>
                    <p style="margin: 10px 0 0 0; color: #111827;">{reason}</p>
                </div>
                
                <p>If you have any questions or would like to discuss this decision, please contact {rejector_name} directly.</p>
                
                <p>You may submit a new request if needed.</p>
                
                <div class="footer">
                    <p>Cell Pool Car Management System</p>
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    subject = f"Vehicle Request #{request_code} Rejected"
    
    return send_email_notification(subject, html_message, [requester.email])
