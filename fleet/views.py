from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
import re
from django.urls import reverse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    Vehicle, CarRequest, HandoverChecklist, Profile, ServiceRecord,
    Ambulance, AmbulanceEquipment, AmbulanceServiceRecord, 
    AmbulanceUsageRecord, AmbulanceRequest, AmbulanceHandoverChecklist
)
from .forms import (
    VehicleForm, DriverAssignmentForm, CarRequestApprovalForm, 
    MileageUpdateForm, HandoverChecklistReviewForm, HandoverCompletionForm, UserProfileForm,
    UserManagementForm, UserProfileManagementForm, PermanentDriverForm, PasswordResetForm, ServiceRecordForm
)


def landing(request):
    """Render the landing page for the Pool Car Manager."""
    return render(request, 'landing.html', {})


def unauthorized_response(request, message=None):
    """Render a friendly unauthorized page instead of redirecting to login.

    This avoids sending already-authenticated users back to the login screen
    (which can feel like a logout) when they simply don't have the role
    required to access a page.
    """
    if message:
        messages.error(request, message)
    return render(request, 'unauthorized.html', {'message': message}, status=403)


def login_page(request):
    """Handle login page and authentication."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Try authenticating directly with the provided identifier
        # (supports username). If that fails and the identifier looks
        # like an email address, try to find the corresponding user
        # by email (case-insensitive) and authenticate using their
        # username. This allows users to login with either username
        # or email + password.
        user = authenticate(request, username=username, password=password)

        if user is None:
            # If input looks like an email address, attempt email lookup
            if username and '@' in username:
                try:
                    user_by_email = User.objects.filter(email__iexact=username).first()
                    if user_by_email:
                        user = authenticate(request, username=user_by_email.username, password=password)
                except Exception:
                    user = None

        if user is not None:
            # Log the user in
            login(request, user)
            
            # Redirect based on user role
            try:
                profile = user.profile
                if profile.role == 'admin':
                    return redirect('fleet:admin_dashboard')
                elif profile.role == 'gm':
                    if profile.subsidiary == 'cellmed':
                        return redirect('fleet:gm_cellmed_dashboard')
                    elif profile.subsidiary == 'cell_insurance':
                        return redirect('fleet:gm_cellinsure_dashboard')
                    elif profile.subsidiary == 'nectacare':
                        return redirect('fleet:gm_nectacare_dashboard')
                    else:
                        return redirect('fleet:gm_cellinsure_dashboard')
                elif profile.role == 'ceo':
                    return redirect('fleet:ceo_dashboard')
                elif profile.role == 'mis':
                    return redirect('fleet:mis_dashboard')
                else:
                    return redirect('fleet:employee_dashboard')
            except Profile.DoesNotExist:
                # If no profile, treat as employee
                return redirect('fleet:employee_dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html', {})


def ambulance_login_page(request):
    """Handle ambulance module login page and authentication."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Try authenticating directly with the provided identifier
        user = authenticate(request, username=username, password=password)

        if user is None:
            # If input looks like an email address, attempt email lookup
            if username and '@' in username:
                try:
                    user_by_email = User.objects.filter(email__iexact=username).first()
                    if user_by_email:
                        user = authenticate(request, username=user_by_email.username, password=password)
                except Exception:
                    user = None

        if user is not None:
            # Check if user has access to ambulance module
            try:
                profile = user.profile
                if profile.module not in ['ambulance', 'both']:
                    messages.error(request, 'You do not have access to the Ambulance Manager module.')
                    return render(request, 'ambulance_login.html', {})
                
                # Log the user in
                login(request, user)
                
                # Redirect based on user role
                if profile.role == 'ambulance_admin':
                    return redirect('fleet:ambulance_admin_dashboard')
                elif profile.role == 'nectacare_head':
                    return redirect('fleet:nectacare_head_dashboard')
                elif profile.role == 'ambulance_mis':
                    return redirect('fleet:ambulance_mis_dashboard')
                else:
                    messages.error(request, 'Invalid role for Ambulance Manager module.')
                    return render(request, 'ambulance_login.html', {})
            except Profile.DoesNotExist:
                messages.error(request, 'Profile not found. Please contact administrator.')
                return render(request, 'ambulance_login.html', {})
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'ambulance_login.html', {})


@login_required
def employee_dashboard(request):
    """Employee dashboard with sidebar navigation."""
    # Redirect non-employees to their correct dashboard using select_related for single query
    try:
        profile = request.user.profile
        if profile.role == 'admin':
            return redirect('fleet:admin_dashboard')
        elif profile.role == 'gm':
            if profile.subsidiary == 'cellmed':
                return redirect('fleet:gm_cellmed_dashboard')
            elif profile.subsidiary == 'cell_insurance':
                return redirect('fleet:gm_cellinsure_dashboard')
            elif profile.subsidiary == 'nectacare':
                return redirect('fleet:gm_nectacare_dashboard')
            else:
                return redirect('fleet:gm_cellinsure_dashboard')
        elif profile.role == 'ceo':
            return redirect('fleet:ceo_dashboard')
        elif profile.role == 'mis':
            return redirect('fleet:mis_dashboard')
    except Profile.DoesNotExist:
        pass  # Continue to employee dashboard if no profile
    
    # Get employee's recent requests with assigned vehicle
    recent_requests = CarRequest.objects.filter(
        requester=request.user
    ).select_related('assigned_vehicle').order_by('-created_at')[:5]
    
    # Combine all vehicle count queries into a single query using annotations
    from django.db.models import Q, Count
    available_vehicles = Vehicle.objects.filter(status='available').count()
    
    # Get pending requests count
    pending_requests = CarRequest.objects.filter(
        requester=request.user,
        status='pending'
    ).count()
    
    # Get assigned requests
    assigned_requests = CarRequest.objects.filter(
        requester=request.user,
        status='assigned'
    ).count()
    
    # Get user's full name and role
    user_full_name = request.user.get_full_name() or request.user.username
    try:
        user_role = request.user.profile.get_role_display()
        # Check if user is a manager (can approve requests)
        is_manager = request.user.profile.employee_type == 'MANAGER'
        
        # Get pending approval count if manager
        pending_approval_count = 0
        if is_manager:
            pending_approval_count = CarRequest.objects.filter(
                status='pending',
                supervisor_approved_by__isnull=True,
                selected_supervisor=request.user,
                requester__profile__employee_type='GENERAL_EMPLOYEE'
            ).count()
    except Profile.DoesNotExist:
        user_role = 'Employee'
        is_manager = False
        pending_approval_count = 0
    
    # Total requests by this user (all time)
    total_requests_count = CarRequest.objects.filter(requester=request.user).count()

    context = {
        'user_name': user_full_name,
        'user_role': user_role,
        'is_manager': is_manager,
        'pending_approval_count': pending_approval_count,
        'stats': {
            'available_vehicles': available_vehicles,
            'pending_requests': pending_requests,
            'assigned_requests': assigned_requests,
            'total_requests': total_requests_count
        },
        'recent_requests': recent_requests
    }
    
    return render(request, 'employee/dashboard.html', context)


@login_required
def admin_dashboard(request):
    """Admin dashboard for Fleet Administrator (dynamic user and role verification)."""
    # Enforce admin-only access; redirect other roles back to their dashboards
    try:
        profile = request.user.profile
        if profile.role != 'admin':
            if profile.role == 'employee' or profile.role == 'driver':
                return redirect('fleet:employee_dashboard')
            elif profile.role == 'gm':
                if profile.subsidiary == 'cellmed':
                    return redirect('fleet:gm_cellmed_dashboard')
                elif profile.subsidiary == 'cell_insurance':
                    return redirect('fleet:gm_cellinsure_dashboard')
                elif profile.subsidiary == 'nectacare':
                    return redirect('fleet:gm_nectacare_dashboard')
                else:
                    return redirect('fleet:gm_cellinsure_dashboard')
            elif profile.role == 'ceo':
                return redirect('fleet:ceo_dashboard')
            elif profile.role == 'mis':
                return redirect('fleet:mis_dashboard')
            else:
                return redirect('fleet:login_page')
    except Profile.DoesNotExist:
        return redirect('fleet:login_page')

    # Optimize with aggregation to reduce queries
    from django.db.models import Count, Q, Case, When, IntegerField
    
    total_vehicles = Vehicle.objects.count()
    available_vehicles = Vehicle.objects.filter(status='available').count()
    
    # Use single query with annotations instead of separate queries
    user_counts = User.objects.aggregate(
        total_employees=Count('id', filter=Q(profile__role='employee')),
        total_drivers=Count('id', filter=Q(profile__role='driver'))
    )
    total_employees = user_counts['total_employees']
    total_drivers = user_counts['total_drivers']
    
    assigned_vehicles = Vehicle.objects.filter(status='booked').count()
    fleet_utilization = round((assigned_vehicles / total_vehicles * 100), 1) if total_vehicles > 0 else 0
    
    # Use single request aggregation
    request_stats = CarRequest.objects.aggregate(
        pending=Count('id', filter=Q(status='pending')),
        approved_unassigned=Count('id', filter=Q(status='approved', assigned_vehicle__isnull=True))
    )
    pending_requests = request_stats['pending']
    approved_requests = request_stats['approved_unassigned']
    
    pending_handovers = HandoverChecklist.objects.filter(reviewed_by__isnull=True).count()
    maintenance_due = Vehicle.objects.filter(status='maintenance').count()
    
    week_ago = timezone.now() - timedelta(days=7)
    recent_requests = CarRequest.objects.filter(created_at__gte=week_ago).select_related('requester', 'assigned_vehicle').order_by('-created_at')[:5]
    recent_handovers = HandoverChecklist.objects.filter(submitted_at__gte=week_ago).select_related('request', 'request__requester', 'request__assigned_vehicle').order_by('-submitted_at')[:3]

    user_name = (request.user.get_full_name() or request.user.username).strip()
    user_role = 'Administrator'

    context = {
        'user_name': user_name,
        'user_role': user_role,
        'stats': {
            'total_vehicles': total_vehicles,
            'available_vehicles': available_vehicles,
            'total_employees': total_employees,
            'total_drivers': total_drivers,
            'fleet_utilization': fleet_utilization,
            'pending_requests': pending_requests,
            'approved_requests': approved_requests,
            'pending_handovers': pending_handovers,
            'maintenance_due': maintenance_due
        },
        'recent_requests': recent_requests,
        'recent_handovers': recent_handovers
    }
    return render(request, 'admin/dashboard.html', context)
@login_required
def gm_cellmed_dashboard(request):
    """GM dashboard for Cellmed division (dynamic user name)."""
    # Enforce GM-only access; redirect other roles back to their dashboards
    try:
        profile = request.user.profile
        if profile.role != 'gm':
            if profile.role == 'employee':
                return redirect('fleet:employee_dashboard')
            elif profile.role == 'admin':
                return redirect('fleet:admin_dashboard')
            elif profile.role == 'ceo':
                return redirect('fleet:ceo_dashboard')
            elif profile.role == 'mis':
                return redirect('fleet:mis_dashboard')
            elif profile.role == 'driver':
                return redirect('fleet:employee_dashboard')
            else:
                return redirect('fleet:login_page')
    except Profile.DoesNotExist:
        return redirect('fleet:login_page')

    user_name = (request.user.get_full_name() or request.user.username or 'Cellmed GM').strip()
    user_role = 'General Manager - Cellmed'
    # Count requests awaiting GM approval (pending and not yet approved by GM)
    pending_approvals = CarRequest.objects.filter(
        subsidiary='cellmed', status='pending', approver1__isnull=True
    ).count()
    division_vehicles = Vehicle.objects.filter(carrequest__subsidiary='cellmed').distinct().count()
    return render(request, 'executive/gm_cellmed.html', {
        'user_name': user_name,
        'user_role': user_role,
        'division': 'Cellmed',
        'pending_approvals': pending_approvals,
        'pending_approval_count': pending_approvals,
        'division_vehicles': division_vehicles,
        'active_page': 'home',
        'dashboard_url': 'fleet:gm_cellmed_dashboard',
        'division_logo': 'cellmed_thumb.png'
    })


@login_required
def gm_cellinsure_dashboard(request):
    """GM dashboard for Cell Insurance division (dynamic user name)."""
    # Enforce GM-only access
    try:
        profile = request.user.profile
        if profile.role != 'gm':
            if profile.role == 'employee':
                return redirect('fleet:employee_dashboard')
            elif profile.role == 'admin':
                return redirect('fleet:admin_dashboard')
            elif profile.role == 'ceo':
                return redirect('fleet:ceo_dashboard')
            elif profile.role == 'mis':
                return redirect('fleet:mis_dashboard')
            elif profile.role == 'driver':
                return redirect('fleet:employee_dashboard')
            else:
                return redirect('fleet:login_page')
    except Profile.DoesNotExist:
        return redirect('fleet:login_page')

    user_name = (request.user.get_full_name() or request.user.username or 'Cell Insurance GM').strip()
    user_role = 'General Manager - Cell Insurance'
    # Count requests awaiting GM approval (pending and not yet approved by GM)
    pending_approvals = CarRequest.objects.filter(
        subsidiary='cell_insurance', status='pending', approver1__isnull=True
    ).count()
    division_vehicles = Vehicle.objects.filter(carrequest__subsidiary='cell_insurance').distinct().count()
    return render(request, 'executive/gm_cellinsure.html', {
        'user_name': user_name,
        'user_role': user_role,
        'division': 'Cell Insurance',
        'pending_approvals': pending_approvals,
        'pending_approval_count': pending_approvals,
        'division_vehicles': division_vehicles,
        'active_page': 'home',
        'dashboard_url': 'fleet:gm_cellinsure_dashboard',
        'division_logo': 'cellinsurance_thumb.png'
    })


@login_required
def gm_nectacare_dashboard(request):
    """GM dashboard for Nectacare division (dynamic user name)."""
    # Enforce GM-only access
    try:
        profile = request.user.profile
        if profile.role != 'gm':
            if profile.role == 'employee':
                return redirect('fleet:employee_dashboard')
            elif profile.role == 'admin':
                return redirect('fleet:admin_dashboard')
            elif profile.role == 'ceo':
                return redirect('fleet:ceo_dashboard')
            elif profile.role == 'mis':
                return redirect('fleet:mis_dashboard')
            elif profile.role == 'driver':
                return redirect('fleet:employee_dashboard')
            else:
                return redirect('fleet:login_page')
    except Profile.DoesNotExist:
        return redirect('fleet:login_page')

    user_name = (request.user.get_full_name() or request.user.username or 'Nectacare Head').strip()
    user_role = 'Head of Operations - Nectacare'
    # Count requests awaiting GM approval (pending and not yet approved by GM)
    pending_approvals = CarRequest.objects.filter(
        subsidiary='nectacare', status='pending', approver1__isnull=True
    ).count()
    division_vehicles = Vehicle.objects.filter(carrequest__subsidiary='nectacare').distinct().count()
    return render(request, 'executive/gm_nectacare.html', {
        'user_name': user_name,
        'user_role': user_role,
        'division': 'Nectacare',
        'pending_approvals': pending_approvals,
        'pending_approval_count': pending_approvals,
        'division_vehicles': division_vehicles,
        'active_page': 'home',
        'dashboard_url': 'fleet:gm_nectacare_dashboard',
        'division_logo': 'nectacare_thumb.png'
    })


def gm_analytics(request):
    """GM analytics page - division-specific usage analytics."""
    # Enforce GM-only access; redirect other roles back to their dashboards
    try:
        profile = request.user.profile
        if profile.role != 'gm':
            if profile.role == 'employee' or profile.role == 'driver':
                return redirect('fleet:employee_dashboard')
            elif profile.role == 'admin':
                return redirect('fleet:admin_dashboard')
            elif profile.role == 'ceo':
                return redirect('fleet:ceo_dashboard')
            elif profile.role == 'mis':
                return redirect('fleet:mis_dashboard')
            else:
                return redirect('fleet:login_page')
    except Profile.DoesNotExist:
        return redirect('fleet:login_page')
    
    from django.db.models import Count, Q
    import json
    
    # Determine which division based on user or pass division param
    division = request.GET.get('division', 'Cellmed')
    
    # Map division to dashboard URL, logo, and subsidiary value
    division_map = {
        'Cellmed': {'dashboard_url': 'fleet:gm_cellmed_dashboard', 'logo': 'cellmed_thumb.png', 'subsidiary': 'cellmed'},
        'Cell Insurance': {'dashboard_url': 'fleet:gm_cellinsure_dashboard', 'logo': 'cellinsurance_thumb.png', 'subsidiary': 'cell_insurance'},
        'Nectacare': {'dashboard_url': 'fleet:gm_nectacare_dashboard', 'logo': 'nectacare_thumb.png', 'subsidiary': 'nectacare'},
    }
    
    division_info = division_map.get(division, division_map['Cellmed'])
    subsidiary_filter = division_info['subsidiary']
    
    # Vehicle statistics for this division - vehicles are not owned per-subsidiary in the model,
    # so derive the division's vehicle set from CarRequest relations (vehicles used by that division).
    division_vehicle_qs = Vehicle.objects.filter(carrequest__subsidiary=subsidiary_filter).distinct()
    vehicle_stats = {
        'total': division_vehicle_qs.count(),
        'available': Vehicle.objects.filter(id__in=division_vehicle_qs.values_list('id', flat=True), status='available').count(),
        'booked': Vehicle.objects.filter(id__in=division_vehicle_qs.values_list('id', flat=True), status='booked').count(),
        'maintenance': Vehicle.objects.filter(id__in=division_vehicle_qs.values_list('id', flat=True), status='maintenance').count(),
        'out_of_service': Vehicle.objects.filter(id__in=division_vehicle_qs.values_list('id', flat=True), status='out_of_service').count()
    }
    
    # Request statistics for this division
    division_requests = CarRequest.objects.filter(subsidiary=subsidiary_filter)
    request_stats = {
        'total': division_requests.count(),
        'pending': division_requests.filter(status='pending').count(),
        'approved': division_requests.filter(status='approved').count(),
        'assigned': division_requests.filter(status='assigned').count(),
        'completed': division_requests.filter(status='completed').count(),
        'rejected': division_requests.filter(status='rejected').count()
    }
    
    # Monthly trends (last 6 months)
    monthly_data = []
    labels = []
    for i in range(5, -1, -1):
        month_start = (timezone.now().replace(day=1) - timedelta(days=30*i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        
        count = division_requests.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).count()
        
        monthly_data.append(count)
        labels.append(month_start.strftime('%b %Y'))
    
    # Daily trends (last 30 days)
    daily_labels = []
    daily_data = []
    today = timezone.now().date()
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        day_start = timezone.make_aware(datetime(d.year, d.month, d.day, 0, 0, 0)) if hasattr(timezone, 'make_aware') else datetime(d.year, d.month, d.day, 0, 0, 0)
        day_end = day_start + timedelta(days=1)
        count = division_requests.filter(created_at__gte=day_start, created_at__lt=day_end).count()
        daily_data.append(count)
        daily_labels.append(d.strftime('%d %b'))
    
    # Vehicle status breakdown for this division
    status_breakdown = [
        {'status': 'Available', 'count': vehicle_stats['available']},
        {'status': 'Booked', 'count': vehicle_stats['booked']},
        {'status': 'Maintenance', 'count': vehicle_stats['maintenance']},
        {'status': 'Out of Service', 'count': vehicle_stats['out_of_service']},
    ]

    # Top vehicles for this division (by completed trips within the division)
    top_vehicles = division_vehicle_qs.annotate(
        trip_count=Count('carrequest', filter=Q(carrequest__status='completed', carrequest__subsidiary=subsidiary_filter))
    ).order_by('-trip_count')[:5]
    
    # Current month stats
    current_month = timezone.now().replace(day=1)
    monthly_requests = division_requests.filter(created_at__gte=current_month).count()
    monthly_completed = division_requests.filter(
        status='completed',
        updated_at__gte=current_month
    ).count()
    
    context = {
        'user_name': (request.user.get_full_name() or request.user.username).strip(),
        'user_role': f'General Manager - {division}',
        'division': division,
        'division_logo': division_info['logo'],
        'dashboard_url': division_info['dashboard_url'],
        'vehicle_stats': vehicle_stats,
        'request_stats': request_stats,
        'monthly_chart_data': json.dumps(monthly_data),
        'monthly_chart_labels': json.dumps(labels),
        'daily_chart_data': json.dumps(daily_data),
        'daily_chart_labels': json.dumps(daily_labels),
        'vehicle_status_data': json.dumps([v['count'] for v in status_breakdown]),
        'vehicle_status_labels': json.dumps([v['status'] for v in status_breakdown]),
        'top_vehicles': top_vehicles,
        'monthly_requests': monthly_requests,
        'monthly_completed': monthly_completed,
    }
    
    return render(request, 'executive/gm_analytics.html', context)


def gm_reports(request):
    """GM reports page - division-specific vehicle inventory and trip reports."""
    # Enforce GM-only access; redirect other roles back to their dashboards
    try:
        profile = request.user.profile
        if profile.role != 'gm':
            if profile.role == 'employee' or profile.role == 'driver':
                return redirect('fleet:employee_dashboard')
            elif profile.role == 'admin':
                return redirect('fleet:admin_dashboard')
            elif profile.role == 'ceo':
                return redirect('fleet:ceo_dashboard')
            elif profile.role == 'mis':
                return redirect('fleet:mis_dashboard')
            else:
                return redirect('fleet:login_page')
    except Profile.DoesNotExist:
        return redirect('fleet:login_page')
    
    # Determine which division based on user or pass division param
    division = request.GET.get('division', 'Cellmed')
    
    # Map division to dashboard URL and logo
    division_map = {
        'Cellmed': {'dashboard_url': 'fleet:gm_cellmed_dashboard', 'logo': 'cellmed_thumb.png'},
        'Cell Insurance': {'dashboard_url': 'fleet:gm_cellinsure_dashboard', 'logo': 'cellinsurance_thumb.png'},
        'Nectacare': {'dashboard_url': 'fleet:gm_nectacare_dashboard', 'logo': 'nectacare_thumb.png'},
    }
    
    division_info = division_map.get(division, division_map['Cellmed'])
    
    return render(request, 'executive/gm_reports.html', {
        'user_name': (request.user.get_full_name() or request.user.username).strip(),
        'user_role': f'General Manager - {division}',
        'division': division,
        'division_logo': division_info['logo'],
        'dashboard_url': division_info['dashboard_url']
    })


def gm_pending_approvals(request):
    """GM pending approvals page - shows requests pending GM approval for their division."""
    # Enforce GM-only access; redirect other roles back to their dashboards
    try:
        profile = request.user.profile
        if profile.role != 'gm':
            if profile.role == 'employee' or profile.role == 'driver':
                return redirect('fleet:employee_dashboard')
            elif profile.role == 'admin':
                return redirect('fleet:admin_dashboard')
            elif profile.role == 'ceo':
                return redirect('fleet:ceo_dashboard')
            elif profile.role == 'mis':
                return redirect('fleet:mis_dashboard')
            else:
                return redirect('fleet:login_page')
    except Profile.DoesNotExist:
        return redirect('fleet:login_page')
    
    # Prefer the logged in GM's subsidiary when available
    # Map display names to subsidiary codes used on CarRequest.subsidiary
    display_to_code = {
        'Cellmed': 'cellmed',
        'Cell Insurance': 'cell_insurance',
        'Nectacare': 'nectacare'
    }

    # Determine division from GM profile if possible
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            if profile.role == 'gm' and profile.subsidiary:
                subsidiary_filter = profile.subsidiary
                # Map back to display label
                code_to_display = {v: k for k, v in display_to_code.items()}
                division_label = code_to_display.get(subsidiary_filter, 'Cellmed')
            else:
                # Fallback to query param
                division_label = request.GET.get('division', 'Cellmed')
                subsidiary_filter = display_to_code.get(division_label, 'cellmed')
        except Exception:
            division_label = request.GET.get('division', 'Cellmed')
            subsidiary_filter = display_to_code.get(division_label, 'cellmed')
    else:
        division_label = request.GET.get('division', 'Cellmed')
        subsidiary_filter = display_to_code.get(division_label, 'cellmed')

    # Map division to dashboard URL and logo
    division_map = {
        'Cellmed': {'dashboard_url': 'fleet:gm_cellmed_dashboard', 'logo': 'cellmed_thumb.png'},
        'Cell Insurance': {'dashboard_url': 'fleet:gm_cellinsure_dashboard', 'logo': 'cellinsurance_thumb.png'},
        'Nectacare': {'dashboard_url': 'fleet:gm_nectacare_dashboard', 'logo': 'nectacare_thumb.png'},
    }
    division_info = division_map.get(division_label, division_map['Cellmed'])

    # Get pending requests for this subsidiary that need GM approval
    # GMs approve ALL requests for their division. For out_of_town, CEO will approve after GM.
    # Exclude requests where GM has already approved (approver1 is set)
    pending_requests = CarRequest.objects.filter(
        subsidiary=subsidiary_filter,
        status='pending',
        approver1__isnull=True
    ).order_by('-created_at')

    context = {
        'user_name': (request.user.get_full_name() or request.user.username).strip(),
        'user_role': f'General Manager - {division_label}',
        'division': division_label,
        'division_logo': division_info['logo'],
        'dashboard_url': division_info['dashboard_url'],
        'requests': pending_requests,
        'pending_approval_count': pending_requests.count(),
        'active_page': 'pending',
    }

    return render(request, 'executive/gm_pending_approvals.html', context)


def gm_previous_approvals(request):
    """GM previous approvals page - shows requests previously approved by GM."""
    # Enforce GM-only access
    try:
        profile = request.user.profile
        if profile.role != 'gm':
            if profile.role == 'employee' or profile.role == 'driver':
                return redirect('fleet:employee_dashboard')
            elif profile.role == 'admin':
                return redirect('fleet:admin_dashboard')
            elif profile.role == 'ceo':
                return redirect('fleet:ceo_dashboard')
            elif profile.role == 'mis':
                return redirect('fleet:mis_dashboard')
            else:
                return redirect('fleet:login_page')
    except Profile.DoesNotExist:
        return redirect('fleet:login_page')
    
    # Determine division from GM profile
    display_to_code = {
        'Cellmed': 'cellmed',
        'Cell Insurance': 'cell_insurance',
        'Nectacare': 'nectacare'
    }
    
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            if profile.role == 'gm' and profile.subsidiary:
                subsidiary_filter = profile.subsidiary
                code_to_display = {v: k for k, v in display_to_code.items()}
                division_label = code_to_display.get(subsidiary_filter, 'Cellmed')
            else:
                division_label = request.GET.get('division', 'Cellmed')
                subsidiary_filter = display_to_code.get(division_label, 'cellmed')
        except Exception:
            division_label = request.GET.get('division', 'Cellmed')
            subsidiary_filter = display_to_code.get(division_label, 'cellmed')
    else:
        division_label = request.GET.get('division', 'Cellmed')
        subsidiary_filter = display_to_code.get(division_label, 'cellmed')

    division_map = {
        'Cellmed': {'dashboard_url': 'fleet:gm_cellmed_dashboard', 'logo': 'cellmed_thumb.png'},
        'Cell Insurance': {'dashboard_url': 'fleet:gm_cellinsure_dashboard', 'logo': 'cellinsurance_thumb.png'},
        'Nectacare': {'dashboard_url': 'fleet:gm_nectacare_dashboard', 'logo': 'nectacare_thumb.png'},
    }
    division_info = division_map.get(division_label, division_map['Cellmed'])

    # Get requests approved by this GM
    approved_requests = CarRequest.objects.filter(
        subsidiary=subsidiary_filter,
        approver1=request.user
    ).order_by('-created_at')

    context = {
        'user_name': (request.user.get_full_name() or request.user.username).strip(),
        'user_role': f'General Manager - {division_label}',
        'division': division_label,
        'division_logo': division_info['logo'],
        'dashboard_url': division_info['dashboard_url'],
        'requests': approved_requests,
    }

    return render(request, 'executive/gm_previous_approvals.html', context)


@login_required
def ceo_dashboard(request):
    """CEO dashboard with company-wide view (dynamic user name)."""
    # Enforce CEO-only access; redirect other roles back to their dashboards
    try:
        profile = request.user.profile
        if profile.role != 'ceo':
            if profile.role == 'employee' or profile.role == 'driver':
                return redirect('fleet:employee_dashboard')
            elif profile.role == 'admin':
                return redirect('fleet:admin_dashboard')
            elif profile.role == 'gm':
                if profile.subsidiary == 'cellmed':
                    return redirect('fleet:gm_cellmed_dashboard')
                elif profile.subsidiary == 'cell_insurance':
                    return redirect('fleet:gm_cellinsure_dashboard')
                elif profile.subsidiary == 'nectacare':
                    return redirect('fleet:gm_nectacare_dashboard')
                else:
                    return redirect('fleet:gm_cellinsure_dashboard')
            elif profile.role == 'mis':
                return redirect('fleet:mis_dashboard')
            else:
                return redirect('fleet:login_page')
    except Profile.DoesNotExist:
        return redirect('fleet:login_page')

    user_name = (request.user.get_full_name() or request.user.username or 'CEO').strip()
    user_role = 'Chief Executive Officer'
    # CEO should see out-of-town requests pending CEO after GM approved
    pending_requests = CarRequest.objects.filter(
        status='pending',
        ceo_approved_by__isnull=True
    ).filter(
        Q(requester__profile__employee_type='MANAGER') |
        Q(out_of_town=True, gm_approved_by__isnull=False)
    )
    pending_approvals = pending_requests.count()
    total_vehicles = Vehicle.objects.count()
    return render(request, 'executive/ceo.html', {
        'user_name': user_name,
        'user_role': user_role,
        'division': 'All Divisions',
        'pending_approvals': pending_approvals,
        'pending_approval_count': pending_approvals,
        'total_vehicles': total_vehicles
    })


@login_required
def ceo_analytics(request):
    """CEO analytics page - company-wide performance metrics (dynamic user name)."""
    # Enforce CEO-only access; redirect other roles back to their dashboards
    try:
        profile = request.user.profile
        if profile.role != 'ceo':
            if profile.role == 'employee' or profile.role == 'driver':
                return redirect('fleet:employee_dashboard')
            elif profile.role == 'admin':
                return redirect('fleet:admin_dashboard')
            elif profile.role == 'gm':
                if profile.subsidiary == 'cellmed':
                    return redirect('fleet:gm_cellmed_dashboard')
                elif profile.subsidiary == 'cell_insurance':
                    return redirect('fleet:gm_cellinsure_dashboard')
                elif profile.subsidiary == 'nectacare':
                    return redirect('fleet:gm_nectacare_dashboard')
                else:
                    return redirect('fleet:gm_cellinsure_dashboard')
            elif profile.role == 'mis':
                return redirect('fleet:mis_dashboard')
            else:
                return redirect('fleet:login_page')
    except Profile.DoesNotExist:
        return redirect('fleet:login_page')
    
    from django.db.models import Count, Q
    import json
    
    # Company-wide vehicle statistics
    vehicle_stats = {
        'total': Vehicle.objects.count(),
        'available': Vehicle.objects.filter(status='available').count(),
        'booked': Vehicle.objects.filter(status='booked').count(),
        'maintenance': Vehicle.objects.filter(status='maintenance').count(),
        'out_of_service': Vehicle.objects.filter(status='out_of_service').count()
    }
    
    # Company-wide request statistics
    request_stats = {
        'total': CarRequest.objects.count(),
        'pending': CarRequest.objects.filter(status='pending').count(),
        'approved': CarRequest.objects.filter(status='approved').count(),
        'assigned': CarRequest.objects.filter(status='assigned').count(),
        'completed': CarRequest.objects.filter(status='completed').count(),
        'rejected': CarRequest.objects.filter(status='rejected').count()
    }
    
    # Monthly trends (last 6 months) - all divisions
    monthly_data = []
    labels = []
    for i in range(5, -1, -1):
        month_start = (timezone.now().replace(day=1) - timedelta(days=30*i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        
        count = CarRequest.objects.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).count()
        
        monthly_data.append(count)
        labels.append(month_start.strftime('%b %Y'))
    
    # Daily trends (last 30 days)
    daily_labels = []
    daily_data = []
    today = timezone.now().date()
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        day_start = timezone.make_aware(datetime(d.year, d.month, d.day, 0, 0, 0)) if hasattr(timezone, 'make_aware') else datetime(d.year, d.month, d.day, 0, 0, 0)
        day_end = day_start + timedelta(days=1)
        count = CarRequest.objects.filter(created_at__gte=day_start, created_at__lt=day_end).count()
        daily_data.append(count)
        daily_labels.append(d.strftime('%d %b'))
    
    # Division breakdown
    division_stats = []
    for subsidiary, name in [('cell_insurance', 'Cell Insurance'), ('cellmed', 'Cellmed'), ('nectacare', 'Nectacare')]:
        # Vehicles used by this subsidiary (derived via CarRequest relation)
        div_vehicles = Vehicle.objects.filter(carrequest__subsidiary=subsidiary).distinct().count()
        div_requests = CarRequest.objects.filter(subsidiary=subsidiary, created_at__gte=timezone.now().replace(day=1)).count()
        division_stats.append({
            'name': name,
            'vehicles': div_vehicles,
            'requests': div_requests
        })
    
    # Vehicle usage by type (company-wide)
    vehicle_usage = list(Vehicle.objects.values('vehicle_type').annotate(count=Count('id')))
    
    # Division comparison for pie chart
    division_requests_data = []
    division_labels = []
    for subsidiary, name in [('cell_insurance', 'Cell Insurance'), ('cellmed', 'Cellmed'), ('nectacare', 'Nectacare')]:
        count = CarRequest.objects.filter(subsidiary=subsidiary, status='completed').count()
        division_requests_data.append(count)
        division_labels.append(name)
    
    # Top vehicles company-wide
    top_vehicles = Vehicle.objects.annotate(
        trip_count=Count('carrequest', filter=Q(carrequest__status='completed'))
    ).order_by('-trip_count')[:8]
    
    # Current month stats
    current_month = timezone.now().replace(day=1)
    monthly_requests = CarRequest.objects.filter(created_at__gte=current_month).count()
    monthly_completed = CarRequest.objects.filter(
        status='completed',
        updated_at__gte=current_month
    ).count()
    
    user_name = (request.user.get_full_name() or request.user.username or 'CEO').strip()
    context = {
        'user_name': user_name,
        'user_role': 'Chief Executive Officer',
        'vehicle_stats': vehicle_stats,
        'request_stats': request_stats,
        'division_stats': division_stats,
        'monthly_chart_data': json.dumps(monthly_data),
        'monthly_chart_labels': json.dumps(labels),
        'daily_chart_data': json.dumps(daily_data),
        'daily_chart_labels': json.dumps(daily_labels),
        'vehicle_usage_data': json.dumps([v['count'] for v in vehicle_usage]),
        'vehicle_usage_labels': json.dumps([v['vehicle_type'] or 'Other' for v in vehicle_usage]),
        'division_requests_data': json.dumps(division_requests_data),
        'division_labels': json.dumps(division_labels),
        'top_vehicles': top_vehicles,
        'monthly_requests': monthly_requests,
        'monthly_completed': monthly_completed,
    }
    
    return render(request, 'executive/ceo_analytics.html', context)


@login_required
def ceo_reports(request):
    """CEO reports page - executive reports and division breakdown (dynamic user name)."""
    # Enforce CEO-only access; redirect other roles back to their dashboards
    try:
        profile = request.user.profile
        if profile.role != 'ceo':
            if profile.role == 'employee' or profile.role == 'driver':
                return redirect('fleet:employee_dashboard')
            elif profile.role == 'admin':
                return redirect('fleet:admin_dashboard')
            elif profile.role == 'gm':
                if profile.subsidiary == 'cellmed':
                    return redirect('fleet:gm_cellmed_dashboard')
                elif profile.subsidiary == 'cell_insurance':
                    return redirect('fleet:gm_cellinsure_dashboard')
                elif profile.subsidiary == 'nectacare':
                    return redirect('fleet:gm_nectacare_dashboard')
                else:
                    return redirect('fleet:gm_cellinsure_dashboard')
            elif profile.role == 'mis':
                return redirect('fleet:mis_dashboard')
            else:
                return redirect('fleet:login_page')
    except Profile.DoesNotExist:
        return redirect('fleet:login_page')
    
    user_name = (request.user.get_full_name() or request.user.username or 'CEO').strip()
    return render(request, 'executive/ceo_reports.html', {
        'user_name': user_name,
        'user_role': 'Chief Executive Officer'
    })


@login_required
def ceo_pending_approvals(request):
    """CEO pending approvals page - requests requiring CEO approval (dynamic user name)."""
    # Enforce CEO-only access; redirect other roles back to their dashboards
    try:
        profile = request.user.profile
        if profile.role != 'ceo':
            if profile.role == 'employee' or profile.role == 'driver':
                return redirect('fleet:employee_dashboard')
            elif profile.role == 'admin':
                return redirect('fleet:admin_dashboard')
            elif profile.role == 'gm':
                if profile.subsidiary == 'cellmed':
                    return redirect('fleet:gm_cellmed_dashboard')
                elif profile.subsidiary == 'cell_insurance':
                    return redirect('fleet:gm_cellinsure_dashboard')
                elif profile.subsidiary == 'nectacare':
                    return redirect('fleet:gm_nectacare_dashboard')
                else:
                    return redirect('fleet:gm_cellinsure_dashboard')
            elif profile.role == 'mis':
                return redirect('fleet:mis_dashboard')
            else:
                return redirect('fleet:login_page')
    except Profile.DoesNotExist:
        return redirect('fleet:login_page')
    
    # CEO should see:
    # 1. All Manager requests (Managers go directly to CEO)
    # 2. Legacy out-of-town requests from General Employees after GM approval
    pending_requests = CarRequest.objects.filter(
        status='pending',
        ceo_approved_by__isnull=True
    ).filter(
        Q(requester__profile__employee_type='MANAGER') |
        Q(out_of_town=True, gm_approved_by__isnull=False)
    ).select_related('requester', 'requester__profile').order_by('-created_at')
    user_name = (request.user.get_full_name() or request.user.username or 'CEO').strip()
    context = {
        'requests': pending_requests,
        'pending_approval_count': pending_requests.count(),
        'user_name': user_name,
        'user_role': 'Chief Executive Officer'
    }
    return render(request, 'executive/ceo_pending_approvals.html', context)


def ceo_previous_approvals(request):
    """CEO previous approvals page - requests previously approved by CEO."""
    # Enforce CEO-only access
    try:
        profile = request.user.profile
        if profile.role != 'ceo':
            if profile.role == 'employee' or profile.role == 'driver':
                return redirect('fleet:employee_dashboard')
            elif profile.role == 'admin':
                return redirect('fleet:admin_dashboard')
            elif profile.role == 'gm':
                if profile.subsidiary == 'cellmed':
                    return redirect('fleet:gm_cellmed_dashboard')
                elif profile.subsidiary == 'cell_insurance':
                    return redirect('fleet:gm_cellinsure_dashboard')
                elif profile.subsidiary == 'nectacare':
                    return redirect('fleet:gm_nectacare_dashboard')
                else:
                    return redirect('fleet:gm_cellinsure_dashboard')
            elif profile.role == 'mis':
                return redirect('fleet:mis_dashboard')
            else:
                return redirect('fleet:login_page')
    except Profile.DoesNotExist:
        return redirect('fleet:login_page')
    
    # Get requests approved by CEO
    approved_requests = CarRequest.objects.filter(
        approver2=request.user
    ).select_related('requester').order_by('-created_at')
    
    user_name = (request.user.get_full_name() or request.user.username or 'CEO').strip()
    context = {
        'requests': approved_requests,
        'user_name': user_name,
        'user_role': 'Chief Executive Officer'
    }
    return render(request, 'executive/ceo_previous_approvals.html', context)


@login_required
def mis_dashboard(request):
    """MIS Admin dashboard for system user management (dynamic user name)."""
    # Restrict access to MIS role only - redirect others to their dashboard
    if hasattr(request.user, 'profile') and request.user.profile.role != 'mis':
        role = request.user.profile.role
        subsidiary = request.user.profile.subsidiary
        if role == 'employee':
            return redirect('fleet:employee_dashboard')
        elif role == 'admin':
            return redirect('fleet:admin_dashboard')
        elif role == 'gm':
            if subsidiary == 'cell_insurance':
                return redirect('fleet:gm_cellinsure_dashboard')
            elif subsidiary == 'cellmed':
                return redirect('fleet:gm_cellmed_dashboard')
            elif subsidiary == 'nectacare':
                return redirect('fleet:gm_nectacare_dashboard')
        elif role == 'ceo':
            return redirect('fleet:ceo_dashboard')
        # Fallback to login if role unknown
        return redirect('fleet:login_page')
    
    # Get user statistics
    user_stats = {
        'total_users': Profile.objects.count(),
        'employees': Profile.objects.filter(role='employee').count(),
        'admins': Profile.objects.filter(role='admin').count(),
        'gm_users': Profile.objects.filter(role='gm').count(),
        'ceo_users': Profile.objects.filter(role='ceo').count(),
        'drivers': Profile.objects.filter(role='driver').count(),
        'dedicated_drivers': Profile.objects.filter(is_dedicated_driver=True).count(),
        'recent_users': User.objects.filter(profile__isnull=False).order_by('-date_joined')[:5]
    }
    
    # Get system statistics
    system_stats = {
        'total_requests': CarRequest.objects.count(),
        'pending_requests': CarRequest.objects.filter(status='pending').count(),
        'active_assignments': CarRequest.objects.filter(status__in=['assigned', 'approved']).count(),
        'total_vehicles': Vehicle.objects.count()
    }
    
    user_name = (request.user.get_full_name() or request.user.username or 'MIS Admin').strip()
    user_role = 'MIS Admin'
    context = {
        'user_name': user_name,
        'user_role': user_role,
        'division': 'System Administration',
        'user_stats': user_stats,
        'system_stats': system_stats
    }
    return render(request, 'mis/dashboard.html', context)


@login_required
def mis_manage_users(request):
    """Manage all system users (dynamic user name, MIS-only).

    Exclude dedicated drivers from the main users list because
    MIS adds drivers separately via the Manage Drivers screen.
    """
    # Restrict access to MIS role only
    if hasattr(request.user, 'profile') and request.user.profile.role != 'mis':
        return redirect('fleet:employee_dashboard') if request.user.profile.role == 'employee' else redirect('fleet:login_page')
    
    users = User.objects.select_related('profile').exclude(
        profile__is_dedicated_driver=True
    ).order_by('-date_joined')
    
    user_name = (request.user.get_full_name() or request.user.username or 'MIS Admin').strip()
    context = {
        'users': users,
        'user_name': user_name,
        'user_role': 'MIS Admin'
    }
    return render(request, 'mis/manage_users.html', context)


@login_required
def mis_add_user(request):
    """Add a new system user (MIS-only, dynamic user name)."""
    # Restrict access to MIS role only
    if hasattr(request.user, 'profile') and request.user.profile.role != 'mis':
        return redirect('fleet:employee_dashboard') if request.user.profile.role == 'employee' else redirect('fleet:login_page')
    
    if request.method == 'POST':
        user_form = UserManagementForm(request.POST)
        profile_form = UserProfileManagementForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            # Create user
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])
            user.save()
            
            # Create profile
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('fleet:mis_manage_users')
        else:
            # Surface form errors to the user so they understand why the form reloaded
            for field, errors in user_form.errors.items():
                for err in errors:
                    messages.error(request, f"User form - {field}: {err}")
            for field, errors in profile_form.errors.items():
                for err in errors:
                    messages.error(request, f"Profile form - {field}: {err}")
    else:
        user_form = UserManagementForm()
        profile_form = UserProfileManagementForm()
    
    user_name = (request.user.get_full_name() or request.user.username or 'MIS Admin').strip()
    return render(request, 'mis/add_user.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'user_name': user_name,
        'user_role': 'MIS Admin'
    })


@login_required
def mis_edit_user(request, user_id):
    """Edit an existing user (MIS-only, dynamic user name)."""
    # Restrict access to MIS role only
    if hasattr(request.user, 'profile') and request.user.profile.role != 'mis':
        return redirect('fleet:employee_dashboard') if request.user.profile.role == 'employee' else redirect('fleet:login_page')
    
    user = get_object_or_404(User, id=user_id)
    profile, created = Profile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        # Handle user info update
        new_username = (request.POST.get('username') or '').strip()
        if not new_username:
            messages.error(request, 'Username is required.')
            return redirect('fleet:mis_edit_user', user_id=user.id)
        if new_username != user.username and User.objects.filter(username=new_username).exists():
            messages.error(request, 'Username is already taken.')
            return redirect('fleet:mis_edit_user', user_id=user.id)

        user.username = new_username
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()
        
        # Handle profile update
        profile.role = request.POST.get('role')
        profile.subsidiary = request.POST.get('subsidiary')
        profile.employee_type = request.POST.get('employee_type', 'GENERAL_EMPLOYEE')
        profile.is_dedicated_driver = request.POST.get('is_dedicated_driver') == 'on'
        profile.save()
        
        messages.success(request, f'User {user.username} updated successfully!')
        return redirect('fleet:mis_manage_users')
    
    user_name = (request.user.get_full_name() or request.user.username or 'MIS Admin').strip()
    context = {
        'edit_user': user,
        'profile': profile,
        'user_name': user_name,
        'user_role': 'MIS Admin'
    }
    return render(request, 'mis/edit_user.html', context)


@login_required
def mis_manage_drivers(request):
    """Manage drivers (MIS-only, dynamic user name)."""
    # Restrict access to MIS role only
    if hasattr(request.user, 'profile') and request.user.profile.role != 'mis':
        return redirect('fleet:employee_dashboard') if request.user.profile.role == 'employee' else redirect('fleet:login_page')
    
    drivers = Profile.objects.filter(is_dedicated_driver=True).select_related('user')
    
    user_name = (request.user.get_full_name() or request.user.username or 'MIS Admin').strip()
    context = {
        'drivers': drivers,
        'user_name': user_name,
        'user_role': 'MIS Admin'
    }
    return render(request, 'mis/manage_drivers.html', context)


@login_required
def mis_add_driver(request):
    """Add a new driver (MIS-only, dynamic user name)."""
    # Restrict access to MIS role only
    if hasattr(request.user, 'profile') and request.user.profile.role != 'mis':
        return redirect('fleet:employee_dashboard') if request.user.profile.role == 'employee' else redirect('fleet:login_page')
    
    if request.method == 'POST':
        form = PermanentDriverForm(request.POST)
        if form.is_valid():
            # Create user account for the driver (no login required)
            username = f"driver_{form.cleaned_data['first_name']}_{form.cleaned_data['last_name']}".lower().replace(' ', '_')
            
            # Ensure unique username
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1
            
            user = User.objects.create(
                username=username,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                is_active=True
            )
            
            # Create profile
            profile = Profile.objects.create(
                user=user,
                role='driver',
                subsidiary=form.cleaned_data['subsidiary'],
                is_dedicated_driver=True
            )

            messages.success(request, f'Driver {user.get_full_name()} added successfully!')
            return redirect('fleet:mis_manage_drivers')
    else:
        form = PermanentDriverForm()
    
    user_name = (request.user.get_full_name() or request.user.username or 'MIS Admin').strip()
    return render(request, 'mis/add_driver.html', {
        'form': form,
        'user_name': user_name,
        'user_role': 'MIS Admin'
    })


def mis_delete_driver(request, user_id):
    """Delete a dedicated driver (MIS only). Only accepts POST to avoid accidental deletes."""
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            # safety: don't allow deleting the MIS admin
            if user.username == 'MIS':
                messages.error(request, 'Cannot delete MIS admin user!')
            else:
                # ensure this is a dedicated driver before deleting
                profile = getattr(user, 'profile', None)
                if profile and profile.is_dedicated_driver:
                    name = user.get_full_name() or user.username
                    user.delete()
                    messages.success(request, f'Driver {name} deleted successfully!')
                else:
                    messages.error(request, 'User is not a dedicated driver or cannot be deleted here.')
        except User.DoesNotExist:
            messages.error(request, 'Driver not found!')

    return redirect('fleet:mis_manage_drivers')


def mis_reset_password(request):
    """Reset user password or delete user."""
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        if action == 'delete_user' and user_id:
            try:
                user = User.objects.get(id=user_id)
                if user.username != 'MIS':  # Prevent deleting MIS admin
                    username = user.username
                    user.delete()
                    messages.success(request, f'User {username} deleted successfully!')
                else:
                    messages.error(request, 'Cannot delete MIS admin user!')
            except User.DoesNotExist:
                messages.error(request, 'User not found!')
        
        elif action == 'reset_password' and user_id:
            new_password = request.POST.get('new_password')
            if new_password:
                try:
                    user = User.objects.get(id=user_id)
                    user.set_password(new_password)
                    user.save()
                    messages.success(request, f'Password reset successfully for {user.username}!')
                except User.DoesNotExist:
                    messages.error(request, 'User not found!')
            else:
                messages.error(request, 'Password is required!')
        
        return redirect('fleet:mis_reset_password')
    
    # Get all users except the current MIS admin and exclude permanent/dedicated drivers
    users = User.objects.exclude(profile__is_dedicated_driver=True).order_by('username')
    
    user_name = (request.user.get_full_name() or request.user.username or 'MIS Admin').strip()
    return render(request, 'mis/reset_password.html', {
        'users': users,
        'user_name': user_name,
        'user_role': 'MIS Admin'
    })


def mis_audit_logs(request):
    """View system audit logs."""
    # Get ALL user activities and requests (not just recent)
    all_users = User.objects.order_by('-last_login')
    all_requests = CarRequest.objects.order_by('-created_at')
    
    user_name = (request.user.get_full_name() or request.user.username or 'MIS Admin').strip()
    context = {
        'all_users': all_users,
        'all_requests': all_requests,
        'total_users': all_users.count(),
        'total_requests': all_requests.count(),
        'user_name': user_name,
        'user_role': 'MIS Admin'
    }
    return render(request, 'mis/audit_logs.html', context)


# Admin Functionality Views

def add_vehicle(request):
    """Add a new vehicle to the fleet."""
    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.status = 'available'  # Ensure new vehicles are available
            vehicle.save()
            messages.success(request, f'Vehicle {vehicle.reg_number} added successfully!')
            return redirect('fleet:manage_vehicles')
        else:
            # Add form errors to messages for debugging
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = VehicleForm()
    
    context = {
        'form': form,
        'user_name': (request.user.get_full_name() or request.user.username).strip(),
        'user_role': 'Fleet Administrator'
    }
    return render(request, 'admin/add_vehicle.html', context)


def manage_vehicles(request):
    """Manage all vehicles in the fleet."""
    from django.db.models import Q, Prefetch
    
    vehicles = Vehicle.objects.all().order_by('-created_at')
    
    # Enrich each vehicle with current assignment and usage stats
    for vehicle in vehicles:
        # Find current active assignment
        vehicle.current_assignment = CarRequest.objects.filter(
            assigned_vehicle=vehicle,
            status__in=['approved', 'assigned']
        ).select_related('requester').first()
        
        # Count total trips
        vehicle.total_trips = CarRequest.objects.filter(
            assigned_vehicle=vehicle,
            status='completed'
        ).count()
    
    # Calculate stats
    total_vehicles = vehicles.count()
    available_count = vehicles.filter(status='available').count()
    maintenance_count = vehicles.filter(status='maintenance').count()
    out_of_service_count = vehicles.filter(status='out_of_service').count()
    in_use_count = vehicles.filter(status='booked').count()
    
    context = {
        'vehicles': vehicles,
        'total_vehicles': total_vehicles,
        'available_count': available_count,
        'maintenance_count': maintenance_count,
        'out_of_service_count': out_of_service_count,
        'in_use_count': in_use_count,
        'user_name': (request.user.get_full_name() or request.user.username).strip(),
        'user_role': 'Fleet Administrator'
    }
    return render(request, 'admin/manage_vehicles.html', context)


def edit_vehicle(request, vehicle_id):
    """Edit an existing vehicle."""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    
    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, f'Vehicle {vehicle.reg_number} updated successfully!')
            return redirect('fleet:manage_vehicles')
    else:
        form = VehicleForm(instance=vehicle)
    
    return render(request, 'admin/edit_vehicle.html', {
        'form': form, 
        'vehicle': vehicle,
        'user_name': (request.user.get_full_name() or request.user.username).strip(),
        'user_role': 'Fleet Administrator'
    })


def vehicle_details_api(request, vehicle_id):
    """Get detailed vehicle information including usage history (API endpoint)."""
    from django.http import JsonResponse
    
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    
    # Current assignment
    current_assignment = CarRequest.objects.filter(
        assigned_vehicle=vehicle,
        status__in=['approved', 'assigned', 'booked']
    ).select_related('requester').first()
    
    # Usage history (all completed trips)
    usage_history = CarRequest.objects.filter(
        assigned_vehicle=vehicle,
        status='completed'
    ).select_related('requester').order_by('-end_time')[:20]
    
    history_data = [{
        'id': req.id,
        'request_code': req.request_code,
        'driver': req.requester.get_full_name() or req.requester.username,
        'purpose': req.purpose,
        'start_date': req.start_time.strftime('%Y-%m-%d %H:%M'),
        'end_date': req.end_time.strftime('%Y-%m-%d %H:%M'),
        'location': req.location,
        'out_of_town': req.out_of_town
    } for req in usage_history]
    
    data = {
        'id': vehicle.id,
        'reg_number': vehicle.reg_number,
        'model': vehicle.model,
        'vehicle_type': vehicle.vehicle_type,
        'subsidiary': vehicle.subsidiary,
        'branch': vehicle.branch,
        'fuel_type': vehicle.fuel_type,
        'engine_capacity': vehicle.engine_capacity,
        'current_mileage': vehicle.current_mileage,
        'service_interval': vehicle.service_interval_mileage,
        'status': vehicle.status,
        'status_display': vehicle.get_status_display(),
        'accessories': vehicle.accessories,
        'image_url': vehicle.image.url if vehicle.image else None,
        'current_assignment': {
            'driver': current_assignment.requester.get_full_name() or current_assignment.requester.username,
            'purpose': current_assignment.purpose,
            'start_date': current_assignment.start_time.strftime('%Y-%m-%d %H:%M'),
            'end_date': current_assignment.end_time.strftime('%Y-%m-%d %H:%M'),
            'location': current_assignment.location
        } if current_assignment else None,
        'usage_history': history_data,
        'total_trips': len(history_data)
    }
    
    return JsonResponse(data)


def toggle_vehicle_service(request, vehicle_id):
    """Mark vehicle as out of service or bring back to service."""
    if request.method == 'POST':
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        
        if vehicle.status == 'out_of_service':
            vehicle.status = 'available'
            messages.success(request, f'{vehicle.reg_number} is now back in service.')
        else:
            vehicle.status = 'out_of_service'
            messages.warning(request, f'{vehicle.reg_number} marked as out of service.')
        
        vehicle.save()
        return redirect('fleet:manage_vehicles')
    
    return redirect('fleet:manage_vehicles')


def delete_vehicle(request, vehicle_id):
    """Delete a vehicle from the system."""
    if request.method == 'POST':
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        reg_number = vehicle.reg_number
        vehicle.delete()
        messages.success(request, f'Vehicle {reg_number} has been removed from the system.')
        return redirect('fleet:manage_vehicles')
    
    return redirect('fleet:manage_vehicles')


def assign_driver(request):
    """Assign drivers to vehicles."""
    if request.method == 'POST':
        form = DriverAssignmentForm(request.POST)
        if form.is_valid():
            driver = form.cleaned_data['driver']
            vehicle = form.cleaned_data['vehicle']
            destination = form.cleaned_data['destination']
            reason = form.cleaned_data['reason']

            # Ensure driver profile exists
            profile, created = Profile.objects.get_or_create(user=driver)

            # Update vehicle status to booked
            vehicle.status = 'booked'
            vehicle.save()

            # Create a car request record for this assignment (for tracking)
            from datetime import datetime, timedelta
            CarRequest.objects.create(
                requester=driver,
                purpose=reason,
                location=destination,
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(days=1),  # Default 1 day assignment
                status='assigned',
                assigned_vehicle=vehicle,
                subsidiary=profile.subsidiary
            )

            messages.success(request, f'{driver.get_full_name() or driver.username} assigned to {vehicle.reg_number} for {destination}!')
            return redirect('fleet:admin_dashboard')
    else:
        form = DriverAssignmentForm()
    
    return render(request, 'admin/assign_driver.html', {
        'form': form,
        'user_name': (request.user.get_full_name() or request.user.username).strip(),
        'user_role': 'Fleet Administrator'
    })


def manage_requests(request):
    """Manage car requests - approve, reject, assign vehicles."""
    requests = CarRequest.objects.all().order_by('-created_at')
    
    context = {
        'requests': requests,
        'user_name': (request.user.get_full_name() or request.user.username).strip(),
        'user_role': 'Fleet Administrator'
    }
    return render(request, 'admin/manage_requests.html', context)


def vehicle_assignments(request):
    """Show requests awaiting vehicle assignment after approvals."""
    # Get all requests (pending, approved, assigned, rejected, completed)
    all_requests = CarRequest.objects.select_related(
        'requester', 'assigned_vehicle', 'approver1', 'approver2'
    ).order_by('-created_at')
    
    # Get available vehicles for assignment
    available_vehicles = Vehicle.objects.filter(status='available').order_by('reg_number')

    # Count assignable requests: approved requests awaiting vehicle assignment
    assignable_count = CarRequest.objects.filter(
        status='approved',
        assigned_vehicle__isnull=True,
        requester__profile__role='employee'
    ).count()
    
    context = {
        'requests': all_requests,
        'available_vehicles': available_vehicles,
        'assignable_count': assignable_count,
        'user_name': (request.user.get_full_name() or request.user.username).strip(),
        'user_role': 'Fleet Administrator'
    }
    return render(request, 'admin/vehicle_assignments.html', context)


def admin_previous_approvals(request):
    """Show requests previously processed by admin."""
    # Get all requests that have been assigned vehicles by admin
    assigned_requests = CarRequest.objects.filter(
        status__in=['assigned', 'completed'],
        assigned_vehicle__isnull=False
    ).select_related(
        'requester', 'assigned_vehicle', 'approver1', 'approver2'
    ).order_by('-created_at')
    
    context = {
        'requests': assigned_requests,
        'user_name': (request.user.get_full_name() or request.user.username).strip(),
        'user_role': 'Fleet Administrator'
    }
    return render(request, 'admin/previous_approvals.html', context)


def assign_vehicle_to_request(request, request_id):
    """Assign a vehicle to an approved request."""
    car_request = get_object_or_404(CarRequest, id=request_id)
    
    if request.method == 'POST':
        vehicle_id = request.POST.get('vehicle_id')
        
        if not vehicle_id:
            messages.error(request, 'Please select a vehicle to assign.')
            return redirect('fleet:vehicle_assignments')
        
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id, status='available')
            
            # Only assign if request is approved
            if car_request.status != 'approved':
                messages.error(request, 'Request must be approved before vehicle assignment.')
                return redirect('fleet:vehicle_assignments')

            # Enforce NEW approval workflow based on employee type
            if not car_request.is_fully_approved:
                employee_type = car_request.requester_employee_type
                if employee_type == 'GENERAL_EMPLOYEE':
                    if not car_request.supervisor_approved_by:
                        messages.error(request, 'Cannot assign vehicle: Request must be approved by Supervisor first.')
                    elif not car_request.gm_approved_by:
                        messages.error(request, 'Cannot assign vehicle: Request must be approved by GM after Supervisor.')
                    else:
                        messages.error(request, 'Cannot assign vehicle: Request does not have all required approvals.')
                elif employee_type == 'MANAGER':
                    if not car_request.ceo_approved_by:
                        messages.error(request, 'Cannot assign vehicle: Manager request must be approved by CEO first.')
                    else:
                        messages.error(request, 'Cannot assign vehicle: Request does not have required CEO approval.')
                return redirect('fleet:vehicle_assignments')
            
            car_request.assigned_vehicle = vehicle
            car_request.status = 'assigned'
            car_request.save()

            # Only mark vehicle as booked AFTER successful assignment
            vehicle.status = 'booked'
            vehicle.save()
            
            # Create a pickup checklist for this assignment
            HandoverChecklist.objects.get_or_create(
                request=car_request,
                checklist_type='pickup',
                defaults={
                    'approval_status': 'pending',
                    'mileage_kms': vehicle.current_mileage if vehicle.current_mileage else None
                }
            )
            
            # Email notification is automatically sent by signals

            messages.success(request, f'Vehicle {vehicle.reg_number} assigned to request #{car_request.request_code} successfully! Employee must complete pickup checklist before use.')
        except Vehicle.DoesNotExist:
            messages.error(request, 'Selected vehicle is not available.')
    
    return redirect('fleet:vehicle_assignments')


def approve_request(request, request_id):
    """Approve a car request and assign vehicle."""
    car_request = get_object_or_404(CarRequest, id=request_id)
    
    if request.method == 'POST':
        form = CarRequestApprovalForm(request.POST, instance=car_request)
        if form.is_valid():
            approved_request = form.save(commit=False)

            # If admin attempts to mark as approved or assign, enforce NEW approval workflow
            if approved_request.status == 'approved':
                if not approved_request.is_fully_approved:
                    employee_type = approved_request.requester_employee_type
                    if employee_type == 'GENERAL_EMPLOYEE':
                        messages.error(request, 'Cannot mark Approved until Supervisor and GM have approved.')
                    elif employee_type == 'MANAGER':
                        messages.error(request, 'Cannot mark Approved until CEO has approved.')
                    return redirect('fleet:approve_request', request_id=request_id)

            # Persist status/assignment changes now that validations passed
            approved_request.save()

            if approved_request.status == 'approved' and approved_request.assigned_vehicle:
                # Update vehicle status and set request to assigned
                approved_request.assigned_vehicle.status = 'booked'
                approved_request.assigned_vehicle.save()
                approved_request.status = 'assigned'
                approved_request.save()
            
            messages.success(request, f'Request #{request_id} processed successfully!')
            return redirect('fleet:manage_requests')
    else:
        form = CarRequestApprovalForm(instance=car_request)
    
    return render(request, 'admin/approve_request.html', {
        'form': form,
        'car_request': car_request,
        'user_name': (request.user.get_full_name() or request.user.username).strip(),
        'user_role': 'Fleet Administrator'
    })


def update_mileage(request):
    """Update vehicle mileage."""
    if request.method == 'POST':
        form = MileageUpdateForm(request.POST)
        if form.is_valid():
            vehicle = form.cleaned_data['vehicle']
            new_mileage = form.cleaned_data['new_mileage']
            notes = form.cleaned_data['notes']
            
            if new_mileage >= vehicle.current_mileage:
                vehicle.current_mileage = new_mileage
                vehicle.save()
                messages.success(request, f'Mileage updated for {vehicle.reg_number}!')
            else:
                messages.error(request, 'New mileage cannot be less than current mileage!')
            
            return redirect('fleet:admin_dashboard')
    else:
        form = MileageUpdateForm()
    
    return render(request, 'admin/update_mileage.html', {
        'form': form,
        'user_name': (request.user.get_full_name() or request.user.username).strip(),
        'user_role': 'Fleet Administrator'
    })


def review_handovers(request):
    """Show all active vehicle assignments (both employees and drivers)."""
    # Get all assigned/booked vehicles - these are active assignments needing handover
    active_assignments = CarRequest.objects.filter(
        status__in=['assigned', 'approved'],
        assigned_vehicle__isnull=False
    ).select_related('requester', 'assigned_vehicle', 'requester__profile').prefetch_related('handover').order_by('-updated_at')
    
    # Get completed handovers awaiting review (include any unreviewed records,
    # even if submitted_at was not set correctly)
    pending_reviews = HandoverChecklist.objects.filter(
        reviewed_by__isnull=True
    ).select_related('request', 'request__requester', 'request__assigned_vehicle').order_by('-submitted_at')
    
    # Get all reviewed handovers (not limited by date)
    completed_reviews = HandoverChecklist.objects.filter(
        reviewed_by__isnull=False
    ).select_related('request', 'request__requester', 'request__assigned_vehicle', 'reviewed_by').order_by('-reviewed_at')
    
    context = {
        'active_assignments': active_assignments,
        'pending_reviews': pending_reviews,
        'completed_reviews': completed_reviews,
        'user_name': (request.user.get_full_name() or request.user.username).strip(),
        'user_role': 'Fleet Administrator'
    }
    return render(request, 'admin/review_handovers.html', context)


def complete_handover(request, request_id):
    """Complete handover process when vehicle is returned."""
    car_request = get_object_or_404(CarRequest, id=request_id)
    
    # Get or create handover checklist
    handover, created = HandoverChecklist.objects.get_or_create(request=car_request)
    
    if request.method == 'POST':
        form = HandoverCompletionForm(request.POST, request.FILES, instance=handover)
        if form.is_valid():
            completed_handover = form.save(commit=False)
            # If admin provided manual return date/time use that to set submitted_at
            rd = form.cleaned_data.get('return_date')
            rt = form.cleaned_data.get('return_time')
            if rd and rt:
                try:
                    naive_dt = datetime.combine(rd, rt)
                    aware_dt = timezone.make_aware(naive_dt, timezone.get_current_timezone())
                    completed_handover.submitted_at = aware_dt
                except Exception:
                    # Fallback to now if conversion fails
                    completed_handover.submitted_at = timezone.now()
            else:
                completed_handover.submitted_at = timezone.now()
            completed_handover.save()
            
            # Update vehicle mileage
            if completed_handover.return_mileage:
                vehicle = car_request.assigned_vehicle
                vehicle.current_mileage = completed_handover.return_mileage
                vehicle.status = 'available'  # Make vehicle available immediately
                vehicle.save()
            
            # Update request status
            car_request.status = 'completed'
            car_request.save()
            
            messages.success(request, f'Handover completed! Vehicle {car_request.assigned_vehicle.reg_number} is now available.')
            return redirect('fleet:review_handovers')
    else:
        form = HandoverCompletionForm(instance=handover)
    
    return render(request, 'admin/complete_handover.html', {
        'form': form,
        'car_request': car_request,
        'handover': handover,
        'user_name': (request.user.get_full_name() or request.user.username).strip(),
        'user_role': 'Fleet Administrator'
    })


def review_handover_detail(request, handover_id):
    """Review a specific handover checklist."""
    handover = get_object_or_404(HandoverChecklist, id=handover_id)
    
    if request.method == 'POST':
        form = HandoverChecklistReviewForm(request.POST, instance=handover)
        if form.is_valid():
            # Get approval status and admin notes from form
            approval_status = request.POST.get('approval_status')
            admin_notes = request.POST.get('admin_notes', '')
            
            # Save to handover object
            handover.reviewed_by = request.user
            handover.reviewed_at = timezone.now()
            handover.approval_status = approval_status
            handover.admin_notes = admin_notes
            handover.save()
            
            # Update vehicle status based on review
            if approval_status == 'approved':
                handover.request.assigned_vehicle.status = 'available'
                handover.request.assigned_vehicle.save()
                handover.request.status = 'completed'
                handover.request.save()
            
            messages.success(request, f'Handover review completed!')
            return redirect('fleet:review_handovers')
    else:
        form = HandoverChecklistReviewForm(instance=handover)
    
    return render(request, 'admin/review_handover_detail.html', {
        'form': form,
        'handover': handover,
        'user_name': (request.user.get_full_name() or request.user.username).strip(),
        'user_role': 'Fleet Administrator'
    })


def previous_handovers(request, vehicle_id):
    """Show previous handover checklists for a specific vehicle."""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    handovers = HandoverChecklist.objects.filter(
        request__assigned_vehicle=vehicle,
        submitted_at__isnull=False
    ).select_related('request', 'request__requester').order_by('-submitted_at')

    context = {
        'vehicle': vehicle,
        'handovers': handovers,
        'user_name': (request.user.get_full_name() or request.user.username).strip(),
        'user_role': 'Fleet Administrator'
    }
    return render(request, 'admin/previous_handovers.html', context)


def fleet_statistics(request):
    """Display comprehensive fleet statistics with enhanced analytics."""
    from django.db.models import Count, Sum, Avg, Q
    from datetime import timedelta
    import json
    
    # Vehicle statistics
    vehicle_stats = {
        'total': Vehicle.objects.count(),
        'available': Vehicle.objects.filter(status='available').count(),
        'booked': Vehicle.objects.filter(status='booked').count(),
        'maintenance': Vehicle.objects.filter(status='maintenance').count(),
        'out_of_service': Vehicle.objects.filter(status='out_of_service').count()
    }
    
    # Request statistics
    request_stats = {
        'total': CarRequest.objects.count(),
        'pending': CarRequest.objects.filter(status='pending').count(),
        'approved': CarRequest.objects.filter(status='approved').count(),
        'assigned': CarRequest.objects.filter(status='assigned').count(),
        'completed': CarRequest.objects.filter(status='completed').count(),
        'rejected': CarRequest.objects.filter(status='rejected').count()
    }
    
    # Monthly statistics (last 6 months for trend chart)
    monthly_data = []
    labels = []
    for i in range(5, -1, -1):
        month_start = (timezone.now().replace(day=1) - timedelta(days=30*i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        
        count = CarRequest.objects.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).count()
        
        monthly_data.append(count)
        labels.append(month_start.strftime('%b %Y'))
    
    # Current month stats
    current_month = timezone.now().replace(day=1)
    monthly_requests = CarRequest.objects.filter(created_at__gte=current_month).count()
    monthly_completed = CarRequest.objects.filter(
        status='completed', 
        updated_at__gte=current_month
    ).count()
    
    # Vehicle usage by type (for pie chart)
    vehicle_usage = list(Vehicle.objects.values('vehicle_type').annotate(count=Count('id')))
    
    # Top 5 most used vehicles
    top_vehicles = Vehicle.objects.annotate(
        trip_count=Count('carrequest', filter=Q(carrequest__status='completed'))
    ).order_by('-trip_count')[:5]
    
    # Daily trends (last 30 days) for admin statistics
    daily_labels = []
    daily_data = []
    today = timezone.now().date()
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        day_start = timezone.make_aware(datetime(d.year, d.month, d.day, 0, 0, 0)) if hasattr(timezone, 'make_aware') else datetime(d.year, d.month, d.day, 0, 0, 0)
        day_end = day_start + timedelta(days=1)
        count = CarRequest.objects.filter(created_at__gte=day_start, created_at__lt=day_end).count()
        daily_data.append(count)
        daily_labels.append(d.strftime('%d %b'))
    
    context = {
        'vehicle_stats': vehicle_stats,
        'request_stats': request_stats,
        'monthly_requests': monthly_requests,
        'monthly_completed': monthly_completed,
        'monthly_chart_data': json.dumps(monthly_data),
        'monthly_chart_labels': json.dumps(labels),
        'daily_chart_data': json.dumps(daily_data),
        'daily_chart_labels': json.dumps(daily_labels),
        'vehicle_usage_data': json.dumps([v['count'] for v in vehicle_usage]),
        'vehicle_usage_labels': json.dumps([v['vehicle_type'] or 'Other' for v in vehicle_usage]),
        'top_vehicles': top_vehicles,
        'user_name': (request.user.get_full_name() or request.user.username).strip(),
        'user_role': 'Fleet Administrator'
    }
    
    return render(request, 'admin/statistics.html', context)


def export_usage_report(request):
    """Export usage and mileage report as Excel file."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ModuleNotFoundError:
        from django.http import HttpResponse
        msg = (
            "Required package 'openpyxl' is not installed on the server.\n"
            "Install it with: python -m pip install openpyxl\n"
            "Or add it to your requirements.txt and run: python -m pip install -r requirements.txt"
        )
        return HttpResponse(msg, status=500, content_type='text/plain')
    from django.http import HttpResponse
    from datetime import datetime, timedelta
    
    # Get report type (weekly or monthly)
    report_type = request.GET.get('type', 'weekly')
    
    # Calculate date range
    end_date = timezone.now()
    if report_type == 'weekly':
        start_date = end_date - timedelta(days=7)
        filename = f'Weekly_Fleet_Report_{end_date.strftime("%Y%m%d")}.xlsx'
        title = f'Weekly Fleet Report ({start_date.strftime("%b %d")} - {end_date.strftime("%b %d, %Y")})'
    else:  # monthly
        start_date = end_date.replace(day=1)
        filename = f'Monthly_Fleet_Report_{end_date.strftime("%Y%m")}.xlsx'
        title = f'Monthly Fleet Report ({end_date.strftime("%B %Y")})'
    
    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Fleet Usage Report'
    
    # Styling
    header_fill = PatternFill(start_color='F59E0B', end_color='F59E0B', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF', size=12)
    title_font = Font(bold=True, size=16, color='1F2937')
    border = Border(
        left=Side(style='thin', color='E5E7EB'),
        right=Side(style='thin', color='E5E7EB'),
        top=Side(style='thin', color='E5E7EB'),
        bottom=Side(style='thin', color='E5E7EB')
    )
    
    # Title
    ws.merge_cells('A1:H1')
    ws['A1'] = title
    ws['A1'].font = title_font
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 30
    
    # Headers
    headers = [
        'Request ID', 'Vehicle Reg', 'Model', 'Driver', 'Start Date', 'End Date',
        'Start Mileage', 'Return Mileage', 'Distance (km)', 'Destination', 'Purpose'
    ]
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=3, column=col)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = border
    
    # Fetch data
    requests = CarRequest.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date,
        assigned_vehicle__isnull=False
    ).select_related('assigned_vehicle', 'requester').order_by('-start_time')
    
    # Data rows
    row = 4
    for req in requests:
        # Attempt to determine start mileage from the most recent handover for this vehicle before this request
        start_mileage = None
        if req.assigned_vehicle:
            prev_handover = HandoverChecklist.objects.filter(
                request__assigned_vehicle=req.assigned_vehicle,
                submitted_at__lt=req.start_time
            ).order_by('-submitted_at').first()
            if prev_handover and prev_handover.return_mileage is not None:
                start_mileage = prev_handover.return_mileage

        # Return mileage recorded on the handover (if any)
        return_mileage = None
        try:
            if hasattr(req, 'handover') and req.handover.return_mileage is not None:
                return_mileage = req.handover.return_mileage
        except Exception:
            return_mileage = None

        # Compute distance if both mileages available
        distance = ''
        if start_mileage is not None and return_mileage is not None:
            try:
                distance = int(return_mileage) - int(start_mileage)
            except Exception:
                distance = ''

        data = [
            f"#{req.id}",
            req.assigned_vehicle.reg_number if req.assigned_vehicle else 'N/A',
            req.assigned_vehicle.model or req.assigned_vehicle.vehicle_type if req.assigned_vehicle else 'N/A',
            req.requester.get_full_name() or req.requester.username,
            req.start_time.strftime('%Y-%m-%d %H:%M') if req.start_time else 'N/A',
            req.end_time.strftime('%Y-%m-%d %H:%M') if req.end_time else 'N/A',
            start_mileage if start_mileage is not None else '',
            return_mileage if return_mileage is not None else '',
            distance,
            req.location or 'N/A',
            req.purpose[:120] + '...' if len(req.purpose) > 120 else req.purpose,
        ]

        for col, value in enumerate(data, start=1):
            cell = ws.cell(row=row, column=col)
            cell.value = value
            cell.border = border
            cell.alignment = Alignment(vertical='center')

        row += 1
    
    # Summary section
    row += 2
    ws.merge_cells(f'A{row}:B{row}')
    ws[f'A{row}'] = 'Summary Statistics'
    ws[f'A{row}'].font = Font(bold=True, size=14)
    
    row += 1
    summary_data = [
        ('Total Requests:', requests.count()),
        ('Completed Trips:', requests.filter(status='completed').count()),
        ('Pending Requests:', requests.filter(status='pending').count()),
        ('Total Vehicles Used:', requests.values('assigned_vehicle').distinct().count()),
    ]
    
    for label, value in summary_data:
        ws[f'A{row}'] = label
        ws[f'B{row}'] = value
        ws[f'A{row}'].font = Font(bold=True)
        row += 1
    
    # Column widths (expanded to match new headers)
    ws.column_dimensions['A'].width = 12  # Request ID
    ws.column_dimensions['B'].width = 15  # Vehicle Reg
    ws.column_dimensions['C'].width = 20  # Model
    ws.column_dimensions['D'].width = 20  # Driver
    ws.column_dimensions['E'].width = 18  # Start Date
    ws.column_dimensions['F'].width = 18  # End Date
    ws.column_dimensions['G'].width = 14  # Start Mileage
    ws.column_dimensions['H'].width = 14  # Return Mileage
    ws.column_dimensions['I'].width = 12  # Distance
    ws.column_dimensions['J'].width = 25  # Destination
    ws.column_dimensions['K'].width = 40  # Purpose
    
    # Create response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    
    return response


# Employee Functionality Views

@login_required
def employee_request_vehicle(request):
    """Employee car request form."""
    if request.method == 'POST':
        try:
            from datetime import datetime
            from django.http import JsonResponse
            
            # Create new car request
            purpose = request.POST.get('purpose')
            start_time_str = request.POST.get('start_time')
            end_time_str = request.POST.get('end_time')
            location = request.POST.get('location')
            subsidiary = request.POST.get('subsidiary')
            out_of_town = request.POST.get('out_of_town') == 'on'
            needs_driver = request.POST.get('needs_driver') == 'on'
            supervisor_id = request.POST.get('supervisor')

            # Validate required fields
            if not purpose or not start_time_str or not end_time_str or not location:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Please fill in all required fields.'})
                messages.error(request, 'Please fill in all required fields.')
                return redirect('fleet:employee_request_vehicle')
            
            # Convert datetime strings to datetime objects
            start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
            end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')

            # Use logged-in user as requester
            requester = request.user
            
            # Get employee type
            employee_type = requester.profile.employee_type if hasattr(requester, 'profile') else 'GENERAL_EMPLOYEE'
            
            # General employees must select a supervisor
            if employee_type == 'GENERAL_EMPLOYEE' and not supervisor_id:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Please select your immediate supervisor.'})
                messages.error(request, 'Please select your immediate supervisor.')
                return redirect('fleet:employee_request_vehicle')

            # Get selected supervisor
            selected_supervisor = None
            if supervisor_id:
                try:
                    selected_supervisor = User.objects.get(id=supervisor_id)
                except User.DoesNotExist:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'message': 'Selected supervisor not found.'})
                    messages.error(request, 'Selected supervisor not found.')
                    return redirect('fleet:employee_request_vehicle')

            # All requests start as 'pending' and go through approval workflow
            car_request = CarRequest.objects.create(
                requester=requester,
                purpose=purpose,
                start_time=start_time,
                end_time=end_time,
                location=location,
                out_of_town=out_of_town,
                needs_driver=needs_driver,
                subsidiary=subsidiary or 'cell_insurance',
                selected_supervisor=selected_supervisor,
                status='pending'
            )

            # Email notifications are automatically sent by signals
            
            success_message = ''
            if employee_type == 'MANAGER':
                # Manager requests go directly to CEO
                success_message = f'Vehicle request submitted successfully! Request ID: #{car_request.request_code}. Your request has been sent to the CEO for approval.'
            else:
                # General employee requests go to selected Supervisor first
                success_message = f'Vehicle request submitted successfully! Request ID: #{car_request.request_code}. Awaiting supervisor approval.'
            
            # Return JSON response for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': success_message,
                    'redirect': reverse('fleet:employee_my_requests')
                })
            
            messages.success(request, success_message)
            return redirect('fleet:employee_dashboard')
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': f'Error submitting request: {str(e)}. Please check your inputs and try again.'})
            messages.error(request, f'Error submitting request: {str(e)}. Please check your inputs and try again.')
            return redirect('fleet:employee_request_vehicle')
    
    # Get user's employee type
    employee_type = request.user.profile.employee_type if hasattr(request.user, 'profile') else 'GENERAL_EMPLOYEE'
    
    # Get list of supervisors (users with Manager employee type, or GM/CEO/Admin roles)
    supervisors = User.objects.filter(
        Q(profile__employee_type='MANAGER') | 
        Q(profile__role__in=['gm', 'ceo', 'admin'])
    ).select_related('profile').order_by('first_name', 'last_name')
    
    # Provide available vehicles to the template for the select dropdown
    available_vehicles = Vehicle.objects.filter(status='available')

    # Preselect vehicle if passed via query string (from Available Vehicles card)
    preselected_vehicle_id = request.GET.get('vehicle_id')
    
    # Check if user is a manager
    is_manager = hasattr(request.user, 'profile') and request.user.profile.employee_type == 'MANAGER'
    
    # Get pending approval count for managers
    pending_approval_count = 0
    if is_manager:
        pending_approval_count = CarRequest.objects.filter(
            selected_supervisor=request.user,
            supervisor_approved_by__isnull=True,
            status='pending'
        ).count()

    return render(request, 'employee/request_vehicle.html', {
        'user_name': request.user.get_full_name() or request.user.username,
        'user_role': 'Employee',
        'available_vehicles': available_vehicles,
        'preselected_vehicle_id': preselected_vehicle_id,
        'supervisors': supervisors,
        'employee_type': employee_type,
        'is_manager': is_manager,
        'pending_approval_count': pending_approval_count
    })


@login_required
def employee_my_requests(request):
    """View employee's car requests."""
    requests = CarRequest.objects.filter(
        requester=request.user
    ).order_by('-created_at')
    
    # Get user's full name
    user_full_name = request.user.get_full_name() or request.user.username
    
    # Check if user is a manager
    is_manager = hasattr(request.user, 'profile') and request.user.profile.employee_type == 'MANAGER'
    
    # Get employee type
    employee_type = request.user.profile.employee_type if hasattr(request.user, 'profile') else 'GENERAL_EMPLOYEE'
    
    # Get pending approval count for managers
    pending_approval_count = 0
    if is_manager:
        pending_approval_count = CarRequest.objects.filter(
            selected_supervisor=request.user,
            supervisor_approved_by__isnull=True,
            status='pending'
        ).count()
    
    context = {
        'requests': requests,
        'user_name': user_full_name,
        'user_role': 'Employee',
        'is_manager': is_manager,
        'employee_type': employee_type,
        'pending_approval_count': pending_approval_count
    }
    return render(request, 'employee/my_requests.html', context)


@login_required
def employee_request_detail(request, request_id):
    """Show detailed view of a single car request to the requester."""
    car_request = get_object_or_404(CarRequest, id=request_id)

    # Only allow the requester or staff to view details
    if car_request.requester != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to view that request.')
        return redirect('fleet:employee_my_requests')

    context = {
        'car_request': car_request,
        'user_name': request.user.get_full_name() or request.user.username,
        'user_role': 'Employee',
        # allow template to decide whether to show edit/cancel actions
        'can_modify': (car_request.requester == request.user and car_request.status == 'pending')
    }
    return render(request, 'employee/request_detail.html', context)


@login_required
def employee_cancel_request(request, request_id):
    """Cancel a pending request."""
    car_request = get_object_or_404(CarRequest, id=request_id)
    
    # Only requester can cancel their own request
    if car_request.requester != request.user:
        messages.error(request, 'You can only cancel your own requests.')
        return redirect('fleet:employee_my_requests')
    
    # Can only cancel if not yet approved/assigned
    if car_request.status in ['pending']:
        car_request.status = 'cancelled'
        car_request.save()
        messages.success(request, f'Request #{car_request.request_code} has been cancelled.')
    else:
        messages.error(request, 'Cannot cancel a request that has already been approved or assigned.')
    
    return redirect('fleet:employee_my_requests')


@login_required
def employee_edit_request(request, request_id):
    """Edit a pending request."""
    car_request = get_object_or_404(CarRequest, id=request_id)
    
    # Only requester can edit their own request
    if car_request.requester != request.user:
        messages.error(request, 'You can only edit your own requests.')
        return redirect('fleet:employee_my_requests')
    
    # Can only edit if still pending
    if car_request.status != 'pending':
        messages.error(request, 'Cannot edit a request that has already been processed.')
        return redirect('fleet:employee_my_requests')
    
    if request.method == 'POST':
        # Update request fields
        car_request.purpose = request.POST.get('purpose')
        car_request.start_time = request.POST.get('start_time')
        car_request.end_time = request.POST.get('end_time')
        car_request.location = request.POST.get('location')
        car_request.subsidiary = request.POST.get('subsidiary')
        car_request.out_of_town = request.POST.get('out_of_town') == 'on'
        car_request.needs_driver = request.POST.get('needs_driver') == 'on'
        car_request.save()
        
        messages.success(request, f'Request #{car_request.request_code} has been updated.')
        return redirect('fleet:employee_my_requests')
    
    # Provide available vehicles for the edit form
    available_vehicles = Vehicle.objects.filter(status='available')
    
    context = {
        'car_request': car_request,
        'available_vehicles': available_vehicles,
        'user_name': request.user.get_full_name() or request.user.username,
        'user_role': 'Employee'
    }
    return render(request, 'employee/edit_request.html', context)


@login_required
def employee_available_vehicles(request):
    """View available vehicles for employees."""
    vehicles = Vehicle.objects.filter(status='available')
    
    # Check if user is a manager
    is_manager = hasattr(request.user, 'profile') and request.user.profile.employee_type == 'MANAGER'
    
    # Get pending approval count for managers
    pending_approval_count = 0
    if is_manager:
        pending_approval_count = CarRequest.objects.filter(
            selected_supervisor=request.user,
            supervisor_approved_by__isnull=True,
            status='pending'
        ).count()
    
    context = {
        'vehicles': vehicles,
        'user_name': request.user.get_full_name() or request.user.username,
        'user_role': 'Employee',
        'is_manager': is_manager,
        'pending_approval_count': pending_approval_count
    }
    return render(request, 'employee/available_vehicles.html', context)


def employee_handover_checklist(request, request_id=None):
    """Employee handover checklist form."""
    car_request = None
    handover_to_edit = None
    
    if request_id:
        car_request = get_object_or_404(CarRequest, id=request_id, requester=request.user)
        # Check if there's an existing handover (for editing rejected ones)
        try:
            handover_to_edit = HandoverChecklist.objects.get(request=car_request, checklist_type='return')
        except HandoverChecklist.DoesNotExist:
            pass
    
    if request.method == 'POST' and car_request:
        # Create or update handover checklist
        handover, created = HandoverChecklist.objects.get_or_create(
            request=car_request,
            checklist_type='return'
        )
        
        # Basic fields
        handover.fuel_level = request.POST.get('fuel_level', '')
        handover.mileage_kms = request.POST.get('mileage_kms')
        handover.fuel_reading = request.POST.get('fuel_reading', '')
        handover.scratches_dents = request.POST.get('scratches_dents', '')
        handover.additional_comments = request.POST.get('additional_comments', '')
        
        # Checklist items - YES/NO fields
        handover.alarm_system_functional = request.POST.get('alarm_system_functional')
        handover.alarm_system_comments = request.POST.get('alarm_system_comments', '')
        
        handover.lock_nuts_spanner = request.POST.get('lock_nuts_spanner')
        handover.lock_nuts_spanner_comments = request.POST.get('lock_nuts_spanner_comments', '')
        
        handover.spare_wheel_hatchet = request.POST.get('spare_wheel_hatchet')
        handover.spare_wheel_hatchet_comments = request.POST.get('spare_wheel_hatchet_comments', '')
        
        handover.seat_belts_functioning = request.POST.get('seat_belts_functioning')
        handover.seat_belts_comments = request.POST.get('seat_belts_comments', '')
        
        handover.hand_brake_functioning = request.POST.get('hand_brake_functioning')
        handover.hand_brake_comments = request.POST.get('hand_brake_comments', '')
        
        handover.view_mirrors_functioning = request.POST.get('view_mirrors_functioning')
        handover.view_mirrors_comments = request.POST.get('view_mirrors_comments', '')
        
        handover.vehicle_insurance_disk = request.POST.get('vehicle_insurance_disk')
        handover.vehicle_insurance_disk_comments = request.POST.get('vehicle_insurance_disk_comments', '')
        
        handover.aa_zimbabwe_card = request.POST.get('aa_zimbabwe_card')
        handover.aa_zimbabwe_card_comments = request.POST.get('aa_zimbabwe_card_comments', '')
        
        handover.vehicle_licence_disk = request.POST.get('vehicle_licence_disk')
        handover.vehicle_licence_disk_comments = request.POST.get('vehicle_licence_disk_comments', '')
        
        handover.brake_lights_functioning = request.POST.get('brake_lights_functioning')
        handover.brake_lights_comments = request.POST.get('brake_lights_comments', '')
        
        handover.indicators_functioning = request.POST.get('indicators_functioning')
        handover.indicators_comments = request.POST.get('indicators_comments', '')
        
        handover.park_lights_functioning = request.POST.get('park_lights_functioning')
        handover.park_lights_comments = request.POST.get('park_lights_comments', '')
        
        handover.spare_wheel = request.POST.get('spare_wheel')
        handover.spare_wheel_comments = request.POST.get('spare_wheel_comments', '')
        
        handover.jack = request.POST.get('jack')
        handover.jack_comments = request.POST.get('jack_comments', '')
        
        handover.wheel_spanner = request.POST.get('wheel_spanner')
        handover.wheel_spanner_comments = request.POST.get('wheel_spanner_comments', '')
        
        handover.tool_box = request.POST.get('tool_box')
        handover.tool_box_comments = request.POST.get('tool_box_comments', '')
        
        handover.wheel_covers = request.POST.get('wheel_covers')
        handover.wheel_covers_comments = request.POST.get('wheel_covers_comments', '')
        
        handover.seat_covers = request.POST.get('seat_covers')
        handover.seat_covers_comments = request.POST.get('seat_covers_comments', '')
        
        handover.reflectors_installed = request.POST.get('reflectors_installed')
        handover.reflectors_installed_comments = request.POST.get('reflectors_installed_comments', '')
        
        handover.car_radio = request.POST.get('car_radio')
        handover.car_radio_comments = request.POST.get('car_radio_comments', '')
        
        handover.floor_mats = request.POST.get('floor_mats')
        handover.floor_mats_comments = request.POST.get('floor_mats_comments', '')
        
        # Handle file upload
        if request.FILES.get('handover_file'):
            handover.checklist_document = request.FILES.get('handover_file')
        
        # Reset approval status to pending when resubmitting
        handover.approval_status = 'pending'
        handover.reviewed_by = None
        handover.reviewed_at = None
        
        # Set submission timestamp
        from django.utils import timezone
        handover.submitted_at = timezone.now()
        handover.save()
        
        # DO NOT mark request as completed yet - admin must review first
        # Request stays 'assigned' until admin approves handover
        
        messages.success(request, f'Handover checklist for request #{car_request.request_code} submitted successfully! Awaiting admin review.')
        return redirect('fleet:employee_handover_checklist')
    
    # Get user's assigned vehicles (requests with assigned_vehicle)
    assigned_vehicles = CarRequest.objects.filter(
        requester=request.user,
        status='assigned',
        assigned_vehicle__isnull=False
    ).select_related('assigned_vehicle')
    
    # For each assigned vehicle, check if handover already exists and add to context
    assigned_vehicles_with_status = []
    for av in assigned_vehicles:
        previous_handover = (
            HandoverChecklist.objects.filter(
                request__assigned_vehicle=av.assigned_vehicle,
                checklist_type='return',
                submitted_at__isnull=False
            )
            .exclude(request=av)
            .select_related('request', 'request__requester')
            .order_by('-submitted_at')
            .first()
        )
        try:
            existing_handover = HandoverChecklist.objects.get(request=av, checklist_type='return')
            # Only show form if rejected or not yet submitted
            can_submit = existing_handover.approval_status == 'rejected' or existing_handover.submitted_at is None
            assigned_vehicles_with_status.append({
                'request': av,
                'has_handover': True,
                'can_submit': can_submit,
                'handover_status': existing_handover.approval_status,
                'handover': existing_handover,
                'previous_handover': previous_handover
            })
        except HandoverChecklist.DoesNotExist:
            # No handover exists yet - show form
            assigned_vehicles_with_status.append({
                'request': av,
                'has_handover': False,
                'can_submit': True,
                'handover_status': None,
                'handover': None,
                'previous_handover': previous_handover
            })
    
    # Get handover history (submitted handovers)
    handover_history = HandoverChecklist.objects.filter(
        request__requester=request.user,
        submitted_at__isnull=False
    ).select_related('request', 'request__assigned_vehicle', 'reviewed_by').order_by('-submitted_at')
    
    # Debug output
    print(f"=== HANDOVER CHECKLIST DEBUG ===")
    print(f"Current user: {request.user.username}")
    print(f"Assigned vehicles count: {assigned_vehicles.count()}")
    for av in assigned_vehicles:
        print(f"  - Request #{av.id}: {av.assigned_vehicle.reg_number if av.assigned_vehicle else 'No vehicle'}")
    
    # Check if user is a manager
    is_manager = hasattr(request.user, 'profile') and request.user.profile.employee_type == 'MANAGER'
    
    # Get pending approval count for managers
    pending_approval_count = 0
    if is_manager:
        pending_approval_count = CarRequest.objects.filter(
            selected_supervisor=request.user,
            supervisor_approved_by__isnull=True,
            status='pending'
        ).count()
    
    context = {
        'car_request': car_request,
        'handover': handover_to_edit,
        'assigned_vehicles_with_status': assigned_vehicles_with_status,
        'handover_history': handover_history,
        'user': request.user,
        'user_name': request.user.get_full_name() or request.user.username,
        'user_role': 'Employee',
        'is_manager': is_manager,
        'pending_approval_count': pending_approval_count
    }
    return render(request, 'employee/handover_checklist.html', context)


@login_required
def employee_pickup_checklist(request, request_id):
    """Employee pickup checklist form - filled out before taking the vehicle."""
    car_request = get_object_or_404(CarRequest, id=request_id, requester=request.user)
    
    # Check if car request has assigned vehicle
    if not car_request.assigned_vehicle:
        messages.error(request, 'No vehicle assigned to this request yet.')
        return redirect('fleet:employee_dashboard')
    
    # Get or create pickup checklist
    pickup_checklist, created = HandoverChecklist.objects.get_or_create(
        request=car_request,
        checklist_type='pickup',
        defaults={'approval_status': 'pending'}
    )
    
    # Check if already submitted
    if pickup_checklist.submitted_at and request.method != 'POST':
        messages.info(request, 'Pickup checklist already submitted.')
        return redirect('fleet:employee_dashboard')
    
    if request.method == 'POST':
        # Save all checklist fields
        pickup_checklist.fuel_level = request.POST.get('fuel_level', '')
        pickup_checklist.mileage_kms = request.POST.get('mileage_kms')
        pickup_checklist.fuel_reading = request.POST.get('fuel_reading', '')
        pickup_checklist.scratches_dents = request.POST.get('scratches_dents', '')
        pickup_checklist.additional_comments = request.POST.get('additional_comments', '')
        
        # Detailed checklist items
        pickup_checklist.alarm_system_functional = request.POST.get('alarm_system_functional')
        pickup_checklist.alarm_system_comments = request.POST.get('alarm_system_comments', '')
        pickup_checklist.lock_nuts_spanner = request.POST.get('lock_nuts_spanner')
        pickup_checklist.lock_nuts_spanner_comments = request.POST.get('lock_nuts_spanner_comments', '')
        pickup_checklist.spare_wheel_hatchet = request.POST.get('spare_wheel_hatchet')
        pickup_checklist.spare_wheel_hatchet_comments = request.POST.get('spare_wheel_hatchet_comments', '')
        pickup_checklist.seat_belts_functioning = request.POST.get('seat_belts_functioning')
        pickup_checklist.seat_belts_comments = request.POST.get('seat_belts_comments', '')
        pickup_checklist.hand_brake_functioning = request.POST.get('hand_brake_functioning')
        pickup_checklist.hand_brake_comments = request.POST.get('hand_brake_comments', '')
        pickup_checklist.view_mirrors_functioning = request.POST.get('view_mirrors_functioning')
        pickup_checklist.view_mirrors_comments = request.POST.get('view_mirrors_comments', '')
        pickup_checklist.vehicle_insurance_disk = request.POST.get('vehicle_insurance_disk')
        pickup_checklist.vehicle_insurance_disk_comments = request.POST.get('vehicle_insurance_disk_comments', '')
        pickup_checklist.aa_zimbabwe_card = request.POST.get('aa_zimbabwe_card')
        pickup_checklist.aa_zimbabwe_card_comments = request.POST.get('aa_zimbabwe_card_comments', '')
        pickup_checklist.vehicle_licence_disk = request.POST.get('vehicle_licence_disk')
        pickup_checklist.vehicle_licence_disk_comments = request.POST.get('vehicle_licence_disk_comments', '')
        pickup_checklist.brake_lights_functioning = request.POST.get('brake_lights_functioning')
        pickup_checklist.brake_lights_comments = request.POST.get('brake_lights_comments', '')
        pickup_checklist.indicators_functioning = request.POST.get('indicators_functioning')
        pickup_checklist.indicators_comments = request.POST.get('indicators_comments', '')
        pickup_checklist.park_lights_functioning = request.POST.get('park_lights_functioning')
        pickup_checklist.park_lights_comments = request.POST.get('park_lights_comments', '')
        pickup_checklist.spare_wheel = request.POST.get('spare_wheel')
        pickup_checklist.spare_wheel_comments = request.POST.get('spare_wheel_comments', '')
        pickup_checklist.jack = request.POST.get('jack')
        pickup_checklist.jack_comments = request.POST.get('jack_comments', '')
        pickup_checklist.wheel_spanner = request.POST.get('wheel_spanner')
        pickup_checklist.wheel_spanner_comments = request.POST.get('wheel_spanner_comments', '')
        pickup_checklist.tool_box = request.POST.get('tool_box')
        pickup_checklist.tool_box_comments = request.POST.get('tool_box_comments', '')
        pickup_checklist.wheel_covers = request.POST.get('wheel_covers')
        pickup_checklist.wheel_covers_comments = request.POST.get('wheel_covers_comments', '')
        pickup_checklist.seat_covers = request.POST.get('seat_covers')
        pickup_checklist.seat_covers_comments = request.POST.get('seat_covers_comments', '')
        pickup_checklist.reflectors_installed = request.POST.get('reflectors_installed')
        pickup_checklist.reflectors_installed_comments = request.POST.get('reflectors_installed_comments', '')
        pickup_checklist.car_radio = request.POST.get('car_radio')
        pickup_checklist.car_radio_comments = request.POST.get('car_radio_comments', '')
        pickup_checklist.floor_mats = request.POST.get('floor_mats')
        pickup_checklist.floor_mats_comments = request.POST.get('floor_mats_comments', '')
        
        # Handle file uploads
        if request.FILES.get('checklist_document'):
            pickup_checklist.checklist_document = request.FILES['checklist_document']
        if request.FILES.get('additional_photo1'):
            pickup_checklist.additional_photo1 = request.FILES['additional_photo1']
        if request.FILES.get('additional_photo2'):
            pickup_checklist.additional_photo2 = request.FILES['additional_photo2']
        if request.FILES.get('additional_photo3'):
            pickup_checklist.additional_photo3 = request.FILES['additional_photo3']
        
        # Set submission timestamp
        pickup_checklist.submitted_at = timezone.now()
        pickup_checklist.approval_status = 'approved'  # Auto-approve pickup checklists
        pickup_checklist.save()
        
        messages.success(request, f'Pickup checklist for {car_request.assigned_vehicle.reg_number} submitted successfully! You can now use the vehicle.')
        return redirect('fleet:employee_dashboard')
    
    # Check if profile exists (for manager check)
    is_manager = False
    if hasattr(request.user, 'profile'):
        is_manager = request.user.profile.employee_type == 'MANAGER'
    
    pending_approval_count = 0
    if is_manager:
        pending_approval_count = CarRequest.objects.filter(
            selected_supervisor=request.user,
            supervisor_approved_by__isnull=True,
            status='pending'
        ).count()
    
    context = {
        'car_request': car_request,
        'pickup_checklist': pickup_checklist,
        'vehicle': car_request.assigned_vehicle,
        'user': request.user,
        'user_name': request.user.get_full_name() or request.user.username,
        'user_role': 'Employee',
        'is_manager': is_manager,
        'pending_approval_count': pending_approval_count
    }
    return render(request, 'employee/pickup_checklist.html', context)


# ============================================
# SUPERVISOR APPROVAL VIEWS (New Workflow)
# ============================================

@login_required
def supervisor_pending_approvals(request):
    """Show pending requests awaiting supervisor approval (for Managers and supervisory roles)."""
    # Get requests where this user was selected as supervisor and approval is pending
    pending_requests = CarRequest.objects.filter(
        status='pending',
        supervisor_approved_by__isnull=True,
        selected_supervisor=request.user,
        requester__profile__employee_type='GENERAL_EMPLOYEE'
    ).select_related('requester', 'requester__profile').order_by('-created_at')
    
    context = {
        'pending_requests': pending_requests,
        'pending_approval_count': pending_requests.count(),
        'user_name': request.user.get_full_name() or request.user.username,
        'user_role': 'Supervisor'
    }
    return render(request, 'supervisor/pending_approvals.html', context)


@login_required
def supervisor_approve_request(request, request_id):
    """Supervisor approve a car request from employee."""
    if request.method != 'POST':
        return redirect('fleet:supervisor_pending_approvals')
    
    try:
        car_request = get_object_or_404(
            CarRequest, 
            id=request_id, 
            status='pending',
            supervisor_approved_by__isnull=True,
            selected_supervisor=request.user,
            requester__profile__employee_type='GENERAL_EMPLOYEE'
        )
        
        # Set supervisor approval
        car_request.supervisor_approved_by = request.user
        car_request.save()
        
        # Email notification sent automatically by signal handler
        messages.success(request, f'Request #{car_request.request_code} approved! Request forwarded to GM for approval.')
    except Exception as e:
        messages.error(request, f'Error approving request: {str(e)}')
    
    return redirect('fleet:supervisor_pending_approvals')


@login_required
def supervisor_reject_request(request, request_id):
    """Supervisor reject a car request from employee."""
    if request.method != 'POST':
        return redirect('fleet:supervisor_pending_approvals')
    
    try:
        car_request = get_object_or_404(
            CarRequest, 
            id=request_id, 
            status='pending',
            supervisor_approved_by__isnull=True,
            selected_supervisor=request.user
        )
        
        # Get rejection reason from form
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        
        if not rejection_reason:
            messages.error(request, 'Please provide a reason for rejection.')
            return redirect('fleet:supervisor_pending_approvals')
        
        # Update request status and add rejection reason
        car_request.status = 'rejected'
        car_request.rejection_reason = rejection_reason
        car_request.save()
        
        # Notify the requester about rejection
        from .email_notifications import notify_rejection
        try:
            notify_rejection(car_request, rejected_by=request.user, reason=rejection_reason)
        except Exception as e:
            # Log email error but don't fail the rejection
            print(f"Failed to send rejection email: {e}")
        
        messages.warning(request, f'Request #{car_request.request_code} has been rejected.')
    except Exception as e:
        messages.error(request, f'Error rejecting request: {str(e)}')
    
    return redirect('fleet:supervisor_pending_approvals')


@login_required
def gm_approve_request(request, request_id):
    """GM approve a car request."""
    print(f"=== GM APPROVE START === ID={request_id} METHOD={request.method} USER={request.user}")
    
    if request.method != 'POST':
        print("Not POST, redirecting")
        return redirect('fleet:gm_pending_approvals')

    try:
        car_request = get_object_or_404(CarRequest, id=request_id, status='pending')
        print(f"Found request: id={car_request.id} status={car_request.status} employee_type={car_request.requester_employee_type}")
        
        # Enforce approval chain for General Employees: Supervisor must approve first
        if car_request.requester_employee_type == 'GENERAL_EMPLOYEE':
            if not car_request.supervisor_approved_by:
                messages.error(request, 'Supervisor must approve this request before GM can review it.')
                return redirect('fleet:gm_pending_approvals')
        
        # Set GM approval
        car_request.gm_approved_by = request.user
        car_request.approver1 = request.user  # Keep for backward compatibility
        
        # General employees: GM approval completes the workflow
        if car_request.requester_employee_type == 'GENERAL_EMPLOYEE':
            car_request.status = 'approved'
            car_request.save()
            
            # Email notification sent automatically by signal handler
            messages.success(request, f'Request #{car_request.request_code} approved! Request is now ready for vehicle assignment.')
        else:
            # This shouldn't happen normally (Managers go to CEO), but handle gracefully
            car_request.status = 'approved'
            car_request.save()
            messages.success(request, f'Request #{car_request.request_code} approved!')
            
        print(f"Updated: status={car_request.status} gm_approved_by={car_request.gm_approved_by}")
        
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Error approving request: {str(e)}')

    print("=== GM APPROVE END ===")
    return redirect('fleet:gm_pending_approvals')


@login_required
def gm_reject_request(request, request_id):
    """GM reject a car request."""
    if request.method != 'POST':
        return redirect('fleet:gm_pending_approvals')
    
    car_request = get_object_or_404(CarRequest, id=request_id, status='pending')
    
    # Get rejection reason from form
    rejection_reason = request.POST.get('rejection_reason', '').strip()
    
    if not rejection_reason:
        messages.error(request, 'Please provide a reason for rejection.')
        return redirect('fleet:gm_pending_approvals')
    
    # Update request status and add rejection reason
    car_request.status = 'rejected'
    car_request.rejection_reason = rejection_reason
    car_request.save()
    
    # Notify the requester about rejection
    from .email_notifications import notify_rejection
    try:
        notify_rejection(car_request, rejected_by=request.user, reason=rejection_reason)
    except Exception as e:
        # Log email error but don't fail the rejection
        print(f"Failed to send rejection email: {e}")
    
    messages.warning(request, f'Request #{car_request.request_code} has been rejected.')
    return redirect('fleet:gm_pending_approvals')


@login_required
def ceo_approve_request(request, request_id):
    """CEO approve a car request (for Managers or out-of-town requests)."""
    print(f"=== CEO APPROVE START === ID={request_id} METHOD={request.method} USER={request.user}")
    
    if request.method != 'POST':
        print("Not POST, redirecting")
        return redirect('fleet:ceo_pending_approvals')
    
    try:
        car_request = get_object_or_404(CarRequest, id=request_id, status='pending')
        print(f"Found request: id={car_request.id} status={car_request.status} employee_type={car_request.requester_employee_type}")
        
        # Managers go directly to CEO - no prior approvals needed
        # For backward compatibility, also handle out-of-town requests that went through GM first
        if car_request.requester_employee_type == 'GENERAL_EMPLOYEE':
            # Legacy out-of-town flow: Enforce that GM approved first
            if not car_request.gm_approved_by and not car_request.approver1:
                print("No GM approval, rejecting")
                messages.error(request, 'GM must approve before CEO can review this request.')
                return redirect('fleet:ceo_pending_approvals')
        
        # Set CEO approval
        car_request.ceo_approved_by = request.user
        car_request.approver2 = request.user  # Keep for backward compatibility
        car_request.status = 'approved'
        car_request.save()
        
        print(f"Updated: status={car_request.status} ceo_approved_by={car_request.ceo_approved_by}")
        
        # Email notification sent automatically by signal handler
        messages.success(request, f'Request #{car_request.request_code} approved! Request is now ready for vehicle assignment.')
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Error approving request: {str(e)}')

    print("=== CEO APPROVE END ===")
    return redirect('fleet:ceo_pending_approvals')


@login_required
def ceo_reject_request(request, request_id):
    """CEO reject a car request."""
    if request.method != 'POST':
        return redirect('fleet:ceo_pending_approvals')
    
    car_request = get_object_or_404(CarRequest, id=request_id, status='pending')
    
    # Get rejection reason from form
    rejection_reason = request.POST.get('rejection_reason', '').strip()
    
    if not rejection_reason:
        messages.error(request, 'Please provide a reason for rejection.')
        return redirect('fleet:ceo_pending_approvals')
    
    # Update request status and add rejection reason
    car_request.status = 'rejected'
    car_request.rejection_reason = rejection_reason
    car_request.save()
    
    # Notify the requester about rejection
    from .email_notifications import notify_rejection
    try:
        notify_rejection(car_request, rejected_by=request.user, reason=rejection_reason)
    except Exception as e:
        # Log email error but don't fail the rejection
        print(f"Failed to send rejection email: {e}")
    
    messages.warning(request, f'Request #{car_request.request_code} has been rejected.')
    return redirect('fleet:ceo_pending_approvals')


@login_required
@login_required
def service_schedule(request):
    """Display vehicle service schedule with maintenance tracking, organized by month."""
    from collections import defaultdict
    from datetime import datetime
    
    # Get all service records ordered by date (most recent first)
    all_service_records = ServiceRecord.objects.all().select_related('vehicle').order_by('-service_date', 'vehicle_reg_number')
    
    # Group records by month
    records_by_month = defaultdict(list)
    
    for record in all_service_records:
        # Format month as "Month Year" (e.g., "January 2026")
        month_key = record.service_date.strftime('%B %Y')
        
        # Get vehicle info
        vehicle = record.vehicle
        reg_number = record.vehicle_reg_number if record.vehicle_reg_number else (vehicle.reg_number if vehicle else 'Unknown')
        description = record.vehicle_description or (vehicle.model if vehicle else '') or (vehicle.vehicle_type if vehicle else 'N/A')
        driver = record.driver_name or 'Pool'
        current_mileage = record.current_mileage or (vehicle.current_mileage if vehicle else 0)
        
        # Calculate KM remaining
        if record.next_service_due and current_mileage:
            km_remaining = record.next_service_due - current_mileage
        elif record.next_service_due:
            km_remaining = record.next_service_due
        else:
            km_remaining = 0
        
        record_data = {
            'id': vehicle.id if vehicle else None,
            'description': description,
            'registration': reg_number,
            'driver': driver,
            'service_date': record.service_date,
            'service_type': record.service_type,
            'service_company': record.service_company,
            'mileage_at_service': record.mileage_at_service or 0,
            'cost': record.cost or 0,
            'next_service_due': record.next_service_due or (record.mileage_at_service + 10000 if record.mileage_at_service else 0),
            'current_mileage': current_mileage,
            'km_remaining': km_remaining,
            'description_text': record.description or '',
            'is_overdue': km_remaining < 0,
            'is_due_soon': 0 <= km_remaining <= 1000,
        }
        
        records_by_month[month_key].append(record_data)
    
    # Convert to list of tuples for template (month_name, records)
    # Sort months in reverse chronological order
    monthly_records = []
    for month_key in sorted(records_by_month.keys(), key=lambda x: datetime.strptime(x, '%B %Y'), reverse=True):
        monthly_records.append({
            'month': month_key,
            'records': records_by_month[month_key]
        })
    
    context = {
        'monthly_records': monthly_records,
        'user_name': request.user.get_full_name() or request.user.username,
        'user_role': 'Fleet Administrator'
    }
    
    return render(request, 'admin/service_schedule.html', context)


@login_required
def export_service_schedule(request):
    """Export service schedule to Excel."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ModuleNotFoundError:
        from django.http import HttpResponse
        msg = (
            "Required package 'openpyxl' is not installed.\n"
            "Install it with: pip install openpyxl"
        )
        return HttpResponse(msg, status=500, content_type='text/plain')
    
    from django.http import HttpResponse
    from datetime import datetime
    
    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Service Schedule'
    
    # Styling
    header_fill = PatternFill(start_color='FED41F', end_color='FED41F', fill_type='solid')
    header_font = Font(bold=True, color='000000', size=11)
    title_font = Font(bold=True, size=14, color='000000')
    border = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )
    
    # Title
    current_month = datetime.now().strftime('%B %Y')
    ws.merge_cells('A1:I1')
    title_cell = ws['A1']
    title_cell.value = f'{current_month.upper()} MILEAGES'
    title_cell.font = title_font
    title_cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Headers
    headers = [
        'VEHICLE DESCRIPTION',
        'REGISTRATION NUMBER',
        'DRIVER',
        'LAST SERVICE MILEAGE',
        'NEXT SERVICE MILEAGE',
        'CURRENT VEHICLE MILEAGE',
        'KM REMAINING BEFORE NEXT SERVICE',
        'Last type of service done',
        'SERVICE COMPANY'
    ]
    
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=2, column=col)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.border = border
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    
    # Get vehicle data
    vehicles = Vehicle.objects.all().order_by('reg_number')
    row = 3
    
    for vehicle in vehicles:
        # Get last completed request for this vehicle
        last_request = CarRequest.objects.filter(
            assigned_vehicle=vehicle,
            status='completed'
        ).order_by('-end_time').first()
        
        driver = "Pool" if not last_request else (
            last_request.requester.get_full_name() or last_request.requester.username
        )
        
        last_service_mileage = vehicle.current_mileage if vehicle.current_mileage else 0
        next_service_mileage = last_service_mileage + (vehicle.service_interval_mileage or 5000)
        km_remaining = next_service_mileage - vehicle.current_mileage if vehicle.current_mileage else next_service_mileage - last_service_mileage
        
        data = [
            vehicle.model or vehicle.vehicle_type,
            vehicle.reg_number,
            driver,
            last_service_mileage,
            next_service_mileage,
            vehicle.current_mileage or 0,
            km_remaining,
            'Not recorded',
            'Not recorded'
        ]
        
        for col, value in enumerate(data, start=1):
            cell = ws.cell(row=row, column=col)
            cell.value = value
            cell.border = border
            cell.alignment = Alignment(vertical='center')
            
            # Highlight overdue or due soon
            if col == 7:  # KM remaining column
                if km_remaining < 0:
                    cell.fill = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')
                    cell.font = Font(bold=True, color='CC0000')
                elif 0 <= km_remaining <= 1000:
                    cell.fill = PatternFill(start_color='FFFFCC', end_color='FFFFCC', fill_type='solid')
                    cell.font = Font(bold=True, color='CC6600')
        
        row += 1
    
    # Adjust column widths
    column_widths = [25, 20, 20, 20, 20, 25, 30, 30, 20]
    for i, width in enumerate(column_widths, start=1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width
    
    # Set row heights
    ws.row_dimensions[1].height = 25
    ws.row_dimensions[2].height = 40
    
    # Create response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f'Service_Schedule_{datetime.now().strftime("%Y%m%d")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response


@login_required
def add_service_record(request):
    """Add a new service record for a vehicle."""
    if request.method == 'POST':
        form = ServiceRecordForm(request.POST)
        if form.is_valid():
            service_record = form.save(commit=False)
            service_record.performed_by = request.user
            service_record.save()
            
            # Get registration number from either vehicle or manual entry
            reg_number = service_record.vehicle.reg_number if service_record.vehicle else service_record.vehicle_reg_number
            messages.success(request, f'Service record added successfully for {reg_number}')
            return redirect('fleet:service_schedule')
    else:
        # Pre-fill vehicle if provided in query params
        vehicle_id = request.GET.get('vehicle')
        initial = {}
        if vehicle_id:
            try:
                vehicle = Vehicle.objects.get(id=vehicle_id)
                initial['vehicle'] = vehicle
                initial['mileage_at_service'] = vehicle.current_mileage
            except Vehicle.DoesNotExist:
                pass
        
        form = ServiceRecordForm(initial=initial)
    
    context = {
        'form': form,
        'user_name': request.user.get_full_name() or request.user.username,
        'user_role': 'Fleet Administrator'
    }
    
    return render(request, 'admin/add_service_record.html', context)


@login_required
def vehicle_service_history(request, vehicle_id):
    """View service history for a specific vehicle."""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    service_records = ServiceRecord.objects.filter(vehicle=vehicle)
    
    context = {
        'vehicle': vehicle,
        'service_records': service_records,
        'user_name': request.user.get_full_name() or request.user.username,
        'user_role': 'Fleet Administrator'
    }
    
    return render(request, 'admin/vehicle_service_history.html', context)


@login_required
def upload_service_excel(request):
    """
    Upload Excel file with service records and automatically import them.
    Expected Excel format:
    - Vehicle Description | Registration Number | Service Date | Service Type | Service Company | Mileage at Service | Cost | Next Service Due | Description
    """
    from openpyxl import load_workbook
    from datetime import datetime
    import csv
    import io
    import tempfile
    import os
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    excel_file = request.FILES.get('excel_file')
    if not excel_file:
        return JsonResponse({'success': False, 'error': 'No file uploaded'})
    
    try:
        records_created = 0
        errors = []
        
        file_name = excel_file.name.lower()
        
        # Handle CSV files
        if file_name.endswith('.csv'):
            file_content = excel_file.read().decode('utf-8-sig')
            csv_reader = csv.reader(io.StringIO(file_content))
            
            # Skip header row
            next(csv_reader, None)
            
            for row_num, row in enumerate(csv_reader, start=2):
                if not any(row):  # Skip empty rows
                    continue
                
                try:
                    # Extract data from columns (including Driver at column 2)
                    # Format: Vehicle Description, Registration Number, Driver, Service Date, Service Type, Service Company, Mileage at Service, Cost, Next Service Due, Description
                    vehicle_description = str(row[0]).strip() if len(row) > 0 and row[0] else None
                    reg_number = str(row[1]).strip() if len(row) > 1 and row[1] else None
                    driver_name = str(row[2]).strip() if len(row) > 2 and row[2] else 'Pool'
                    service_date_raw = row[3] if len(row) > 3 else None
                    service_type = str(row[4]).strip() if len(row) > 4 and row[4] else 'General Repair'
                    service_company = str(row[5]).strip() if len(row) > 5 and row[5] else 'Unknown'
                    mileage = int(float(row[6])) if len(row) > 6 and row[6] and str(row[6]).replace('.', '').replace(',', '').isdigit() else 0
                    cost = float(str(row[7]).replace(',', '')) if len(row) > 7 and row[7] and str(row[7]).replace('.', '').replace(',', '').isdigit() else 0
                    next_service_due = int(float(row[8])) if len(row) > 8 and row[8] and str(row[8]).replace('.', '').replace(',', '').isdigit() else None
                    description = str(row[9]).strip() if len(row) > 9 and row[9] else ''
                    
                    if not reg_number:
                        errors.append(f'Row {row_num}: Missing registration number')
                        continue
                    
                    # Find vehicle by registration number
                    vehicle = Vehicle.objects.filter(reg_number__iexact=reg_number).first()
                    if not vehicle:
                        errors.append(f'Row {row_num}: Vehicle with registration {reg_number} not found')
                        continue
                    
                    # Parse service date
                    if service_date_raw:
                        try:
                            service_date = datetime.strptime(str(service_date_raw), '%Y-%m-%d').date()
                        except:
                            try:
                                service_date = datetime.strptime(str(service_date_raw), '%m/%d/%Y').date()
                            except:
                                try:
                                    service_date = datetime.strptime(str(service_date_raw), '%d/%m/%Y').date()
                                except:
                                    service_date = timezone.now().date()
                    else:
                        service_date = timezone.now().date()
                    
                    # Create service record
                    ServiceRecord.objects.create(
                        vehicle=vehicle,
                        vehicle_reg_number=reg_number,
                        vehicle_description=vehicle_description or '',
                        driver_name=driver_name,
                        service_date=service_date,
                        service_type=service_type,
                        service_company=service_company,
                        mileage_at_service=mileage,
                        cost=cost,
                        next_service_due=next_service_due,
                        description=description,
                        current_mileage=vehicle.current_mileage if vehicle else mileage,
                        performed_by=request.user
                    )
                    
                    records_created += 1
                    
                except Exception as e:
                    errors.append(f'Row {row_num}: {str(e)}')
                    continue
        
        # Handle Excel files (.xlsx, .xls)
        else:
            try:
                # Save uploaded file to a temporary location
                # This ensures openpyxl can read it properly
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    for chunk in excel_file.chunks():
                        tmp_file.write(chunk)
                    tmp_file_path = tmp_file.name
                
                try:
                    # Load the workbook from the temporary file
                    wb = load_workbook(tmp_file_path, data_only=True, read_only=True)
                    ws = wb.active
                except Exception as load_error:
                    # Clean up temp file
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
                    return JsonResponse({
                        'success': False, 
                        'error': f'Unable to read Excel file. Please ensure it is a valid .xlsx file saved in the correct format. Try opening the file in Excel and saving it again.'
                    })
            except Exception as e:
                return JsonResponse({
                    'success': False, 
                    'error': f'Error processing file: {str(e)}'
                })
            
            # Assuming first row is headers, start from row 2
            for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                # Skip completely empty rows (all cells are None or empty)
                if all(cell is None or str(cell).strip() == '' for cell in row):
                    continue
                
                try:
                    # Extract data from columns matching your format:
                    # A: Vehicle Description, B: Registration Number, C: Driver, D: Last Service Mileage
                    # E: Next Service Mileage, F: Current Vehicle Mileage, G: KM Remaining, H: Last type of service done, I: Service Company
                    vehicle_description = str(row[0]).strip() if row[0] and str(row[0]).strip() else 'N/A'
                    # Remove spaces from registration number for matching
                    reg_number_raw = str(row[1]).strip() if row[1] and str(row[1]).strip() else None
                    reg_number = reg_number_raw.replace(' ', '') if reg_number_raw else None
                    driver = str(row[2]).strip() if len(row) > 2 and row[2] and str(row[2]).strip() else 'Pool'
                    
                    # Parse numeric values more robustly
                    def parse_number(value, default=0):
                        if not value or value is None:
                            return default
                        try:
                            # Convert to string and remove commas
                            clean_val = str(value).replace(',', '').replace(' ', '').strip()
                            # Handle negative values in parentheses
                            if clean_val.startswith('(') and clean_val.endswith(')'):
                                clean_val = '-' + clean_val[1:-1]
                            # Handle None string
                            if clean_val.lower() in ('none', 'n/a', '', '-'):
                                return default
                            return int(float(clean_val))
                        except:
                            return default
                    
                    last_service_mileage = parse_number(row[3] if len(row) > 3 else None, 0)
                    next_service_mileage = parse_number(row[4] if len(row) > 4 else None, None)
                    current_mileage = parse_number(row[5] if len(row) > 5 else None, 0)
                    # Column H: Last type of service done
                    service_description = str(row[7]).strip() if len(row) > 7 and row[7] and str(row[7]).strip() else ''
                    # Column I: Service Company
                    service_company_col = str(row[8]).strip() if len(row) > 8 and row[8] and str(row[8]).strip() else 'Not specified'
                    
                    # Skip if no valid registration number
                    if not reg_number or reg_number.lower() in ('none', 'n/a', '', 'registration number', 'registrationnumber'):
                        errors.append(f'Row {row_num}: Skipped - No valid registration number (got: {reg_number_raw})')
                        continue
                    
                    # Try to find vehicle in main system - try with and without spaces
                    vehicle = Vehicle.objects.filter(reg_number__iexact=reg_number).first()
                    if not vehicle:
                        # Try with original spacing
                        vehicle = Vehicle.objects.filter(reg_number__iexact=reg_number_raw).first()
                    
                    # Use current date as service date since your Excel doesn't have a service date column
                    service_date = timezone.now().date()
                    
                    # Extract month from headfrom description (column H)
                    service_type = 'General Service'
                    service_company = service_company_col if service_company_col != 'Not specified' else 'Not specified'
                    
                    if service_description:
                        desc_lower = service_description.lower()
                        # Extract the most recent service type from description
                        # Look for patterns like "B service June 2022 /C Service Nov 2022"
                        if 'first service' in desc_lower:
                            service_type = 'First Service'
                        elif 'c service' in desc_lower or 'c srvice' in desc_lower:
                            service_type = 'C Service'
                        elif 'b service' in desc_lower or 'b srvice' in desc_lower:
                            service_type = 'B Service'
                        elif 'a service' in desc_lower:
                            service_type = 'A Service'
                        elif 'oil change' in desc_lower:
                            service_type = 'Oil Change'
                        elif 'major service' in desc_lower:
                            service_type = 'Major Service'
                        else:
                            # If description exists but no service type found, use as-is (limited to first 64 chars)
                            service_type = service_description[:64] if len(service_description) <= 64 else 'General Repair'
                    
                    # Set next service due if not provided
                    if not next_service_mileage and last_service_mileage:
                        next_service_mileage = last_service_mileage + 10000  # Default 10k interval
                    
                    # Create service record - works with or without vehicle in main system
                    ServiceRecord.objects.create(
                        vehicle=vehicle,  # Can be None
                        vehicle_reg_number=reg_number,
                        vehicle_description=vehicle_description or '',
                        driver_name=driver or '',
                        current_mileage=current_mileage,
                        upload_month=upload_month,
                        service_date=service_date,
                        service_type=service_type,
                        service_company=service_company,
                        mileage_at_service=last_service_mileage,
                        cost=0,  # No cost column in your format
                        next_service_due=next_service_mileage,
                        description=service_description,
                        performed_by=request.user
                    )
                    
                    records_created += 1
                    
                except Exception as e:
                    error_msg = f'Row {row_num} (Reg: {reg_number_raw if "reg_number_raw" in locals() else "unknown"}): {str(e)}'
                    errors.append(error_msg)
                    print(f"ERROR processing Excel row {row_num}: {str(e)}")  # Log to console for debugging
                    import traceback
                    traceback.print_exc()  # Print full traceback for debugging
                    continue
            
            # Clean up temporary file
            try:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
            except:
                pass  # Ignore cleanup errors
        
        response_data = {
            'success': True,
            'records_created': records_created,
            'errors': errors if errors else None,
            'total_rows_processed': row_num - 1 if 'row_num' in locals() else 0
        }
        
        if errors:
            response_data['error_details'] = errors[:10]  # Show first 10 errors
        
        if errors and records_created == 0:
            response_data['success'] = False
            response_data['error'] = f'Failed to import any records. Please check the Excel format. Errors: {"; ".join(errors[:3])}'
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error processing file: {str(e)}'})


# ============================================
# AMBULANCE MANAGER VIEWS
# ============================================

@login_required
def ambulance_admin_dashboard(request):
    """Ambulance Admin dashboard - main control center."""
    # Check authorization
    try:
        profile = request.user.profile
        if profile.role != 'ambulance_admin' or profile.module not in ['ambulance', 'both']:
            return unauthorized_response(request, 'You do not have access to the Ambulance Admin dashboard.')
    except Profile.DoesNotExist:
        return unauthorized_response(request, 'Profile not found.')
    
    # Get statistics
    total_ambulances = Ambulance.objects.count()
    available_ambulances = Ambulance.objects.filter(status='available').count()
    on_call = Ambulance.objects.filter(status='on_call').count()
    in_maintenance = Ambulance.objects.filter(status='maintenance').count()
    
    # Recent ambulances
    recent_ambulances = Ambulance.objects.all().order_by('-created_at')[:5]
    
    # Service due alerts
    ambulances_needing_service = Ambulance.objects.filter(
        service_interval_mileage__isnull=False
    ).exclude(status='out_of_service')
    
    service_alerts = []
    for amb in ambulances_needing_service:
        if amb.is_service_due:
            service_alerts.append(amb)
    
    # Recent usage records
    recent_usage = AmbulanceUsageRecord.objects.select_related('ambulance', 'driver').order_by('-date')[:10]
    
    # Pending requests (if applicable)
    pending_requests = AmbulanceRequest.objects.filter(status='pending').order_by('-created_at')[:5]
    
    context = {
        'total_ambulances': total_ambulances,
        'available_ambulances': available_ambulances,
        'on_call': on_call,
        'in_maintenance': in_maintenance,
        'recent_ambulances': recent_ambulances,
        'service_alerts': service_alerts,
        'recent_usage': recent_usage,
        'pending_requests': pending_requests,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'ambulance/admin_dashboard.html', context)


@login_required
def nectacare_head_dashboard(request):
    """Nectacare Head dashboard - read-only view with reports and approval."""
    # Check authorization
    try:
        profile = request.user.profile
        if profile.role != 'nectacare_head' or profile.module not in ['ambulance', 'both']:
            return unauthorized_response(request, 'You do not have access to the Nectacare Head dashboard.')
    except Profile.DoesNotExist:
        return unauthorized_response(request, 'Profile not found.')
    
    # Get statistics
    total_ambulances = Ambulance.objects.count()
    available_ambulances = Ambulance.objects.filter(status='available').count()
    on_call = Ambulance.objects.filter(status='on_call').count()
    
    # Recent ambulances with status
    recent_ambulances = Ambulance.objects.all().order_by('-updated_at')[:10]
    
    # Service history
    recent_services = AmbulanceServiceRecord.objects.select_related('ambulance').order_by('-service_date')[:10]
    
    # Usage reports
    from django.db.models import Sum, Avg, Count, F
    from django.utils import timezone
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    usage_stats = AmbulanceUsageRecord.objects.filter(date__gte=thirty_days_ago).aggregate(
        total_distance=Sum(F('end_mileage') - F('start_mileage')),
        total_trips=Count('id'),
        total_fuel_cost=Sum('fuel_cost')
    )
    
    # Pending approval requests
    pending_requests = AmbulanceRequest.objects.filter(status='pending').order_by('-created_at')
    
    context = {
        'total_ambulances': total_ambulances,
        'available_ambulances': available_ambulances,
        'on_call': on_call,
        'recent_ambulances': recent_ambulances,
        'recent_services': recent_services,
        'usage_stats': usage_stats,
        'pending_requests': pending_requests,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'ambulance/nectacare_head_dashboard.html', context)


@login_required
def ambulance_manage_fleet(request):
    """Manage ambulance fleet - list all ambulances."""
    try:
        profile = request.user.profile
        if profile.role != 'ambulance_admin':
            return unauthorized_response(request, 'Access denied.')
    except Profile.DoesNotExist:
        return unauthorized_response(request, 'Profile not found.')
    
    ambulances = Ambulance.objects.all().order_by('reg_number')
    
    # Fetch all ambulance usage records (assignments)
    assignments = AmbulanceUsageRecord.objects.select_related(
        'ambulance', 'driver'
    ).order_by('-date', '-created_at')[:50]  # Show last 50 assignments
    
    context = {
        'ambulances': ambulances,
        'assignments': assignments,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'ambulance/manage_fleet.html', context)


@login_required
def ambulance_add(request):
    """Add a new ambulance."""
    try:
        profile = request.user.profile
        if profile.role != 'ambulance_admin':
            return unauthorized_response(request, 'Access denied.')
    except Profile.DoesNotExist:
        return unauthorized_response(request, 'Profile not found.')
    
    if request.method == 'POST':
        # Handle form submission
        reg_number = request.POST.get('reg_number')
        model = request.POST.get('model')
        year = request.POST.get('year')
        status = request.POST.get('status', 'available')
        service_interval = request.POST.get('service_interval_mileage')
        current_mileage = request.POST.get('current_mileage', 0)
        base_location = request.POST.get('base_location')
        
        try:
            ambulance = Ambulance.objects.create(
                reg_number=reg_number,
                model=model,
                year=year if year else None,
                status=status,
                service_interval_mileage=service_interval if service_interval else None,
                current_mileage=current_mileage if current_mileage else 0,
                base_location=base_location
            )
            
            # Handle image upload
            if request.FILES.get('image'):
                ambulance.image = request.FILES['image']
                ambulance.save()
            
            messages.success(request, f'Ambulance {reg_number} added successfully!')
            return redirect('fleet:ambulance_manage_fleet')
        except Exception as e:
            messages.error(request, f'Error adding ambulance: {str(e)}')
    
    context = {
        'user_name': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'ambulance/add_ambulance.html', context)


@login_required
def ambulance_assign_driver(request):
    """Assign a driver to an ambulance for deployment."""
    try:
        profile = request.user.profile
        if profile.role != 'ambulance_admin':
            return unauthorized_response(request, 'Access denied.')
    except Profile.DoesNotExist:
        return unauthorized_response(request, 'Profile not found.')
    
    if request.method == 'POST':
        ambulance_id = request.POST.get('ambulance_id')
        driver_id = request.POST.get('driver_id')
        opening_mileage = request.POST.get('opening_mileage')
        purpose = request.POST.get('purpose')
        
        try:
            ambulance = Ambulance.objects.get(id=ambulance_id)
            driver = User.objects.get(id=driver_id)
            
            # Get driver's full name
            driver_name = driver.get_full_name() or driver.username
            
            # Update ambulance to "on_call" status
            ambulance.status = 'on_call'
            ambulance.save()
            
            # Create a usage record with opening mileage
            AmbulanceUsageRecord.objects.create(
                ambulance=ambulance,
                driver=driver,
                purpose=purpose,
                start_mileage=opening_mileage,
                driver_name=driver_name,
                driver_phone=''
            )
            
            messages.success(request, f'Driver "{driver_name}" assigned to {ambulance.reg_number}. Ambulance marked as On Call.')
            return redirect('fleet:ambulance_record_usage')
        except Exception as e:
            messages.error(request, f'Error assigning driver: {str(e)}')
            return redirect('fleet:ambulance_record_usage')
    
    return redirect('fleet:ambulance_record_usage')


def ambulance_record_usage(request):
    """Record ambulance usage and closing mileage upon return."""
    try:
        profile = request.user.profile
        if profile.role != 'ambulance_admin':
            return unauthorized_response(request, 'Access denied.')
    except Profile.DoesNotExist:
        return unauthorized_response(request, 'Profile not found.')
    
    if request.method == 'POST':
        ambulance_id = request.POST.get('ambulance_id')
        closing_mileage = request.POST.get('closing_mileage')
        fuel_added = request.POST.get('fuel_added')
        fuel_cost = request.POST.get('fuel_cost')
        notes = request.POST.get('notes')
        
        try:
            ambulance = Ambulance.objects.get(id=ambulance_id)
            
            # Get the latest active usage record for this ambulance
            usage_record = AmbulanceUsageRecord.objects.filter(
                ambulance=ambulance,
                end_mileage__isnull=True
            ).latest('created_at')
            
            # Update the usage record with closing mileage
            usage_record.end_mileage = closing_mileage
            usage_record.fuel_added = fuel_added if fuel_added else None
            usage_record.fuel_cost = fuel_cost if fuel_cost else None
            usage_record.notes = notes if notes else None
            usage_record.save()
            
            # Update ambulance mileage and status back to available
            ambulance.current_mileage = closing_mileage
            ambulance.status = 'available'
            ambulance.save()
            
            # Handle receipt upload
            if request.FILES.get('fuel_receipt'):
                usage_record.fuel_receipt = request.FILES['fuel_receipt']
                usage_record.save()
            
            messages.success(request, 'Usage record updated successfully! Ambulance marked as Available.')
            return redirect('fleet:ambulance_admin_dashboard')
        except AmbulanceUsageRecord.DoesNotExist:
            messages.error(request, 'No active trip found for this ambulance. Please assign a driver first.')
            return redirect('fleet:ambulance_record_usage')
        except Exception as e:
            messages.error(request, f'Error recording usage: {str(e)}')
            return redirect('fleet:ambulance_record_usage')
    
    ambulances = Ambulance.objects.all().order_by('reg_number')
    
    # Get all ambulance drivers
    drivers = User.objects.filter(
        profile__role='driver',
        profile__module__in=['ambulance', 'both'],
        profile__is_dedicated_driver=True
    ).select_related('profile').order_by('first_name', 'last_name')
    
    context = {
        'ambulances': ambulances,
        'drivers': drivers,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'ambulance/record_usage.html', context)


@login_required
def ambulance_view_statistics(request):
    """View ambulance usage statistics and reports."""
    try:
        profile = request.user.profile
        if profile.role not in ['ambulance_admin', 'nectacare_head']:
            return unauthorized_response(request, 'Access denied.')
    except Profile.DoesNotExist:
        return unauthorized_response(request, 'Profile not found.')
    
    from django.db.models import Sum, Avg, Count, F
    from django.utils import timezone
    from datetime import timedelta
    import json
    
    # Calculate statistics for different time periods
    thirty_days_ago = timezone.now() - timedelta(days=30)
    ninety_days_ago = timezone.now() - timedelta(days=90)
    
    # Monthly statistics
    monthly_stats = AmbulanceUsageRecord.objects.filter(date__gte=thirty_days_ago).aggregate(
        total_trips=Count('id'),
        total_distance=Sum(F('end_mileage') - F('start_mileage')),
        total_fuel_cost=Sum('fuel_cost'),
        avg_distance=Avg(F('end_mileage') - F('start_mileage'))
    )
    
    # Quarterly statistics
    quarterly_stats = AmbulanceUsageRecord.objects.filter(date__gte=ninety_days_ago).aggregate(
        total_trips=Count('id'),
        total_distance=Sum(F('end_mileage') - F('start_mileage')),
        total_fuel_cost=Sum('fuel_cost')
    )

    # Monthly trends (last 6 months)
    monthly_data = []
    monthly_labels = []
    today = timezone.now().date()
    for i in range(5, -1, -1):
        month_start = (today.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        count = AmbulanceUsageRecord.objects.filter(date__gte=month_start, date__lt=month_end).count()
        monthly_data.append(count)
        monthly_labels.append(month_start.strftime('%b %Y'))

    # Daily activity (last 30 days)
    daily_labels = []
    daily_data = []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        daily_labels.append(day.strftime('%d %b'))
        daily_data.append(AmbulanceUsageRecord.objects.filter(date=day).count())

    # Ambulance status distribution
    status_counts = list(Ambulance.objects.values('status').annotate(count=Count('id')))
    status_label_map = dict(Ambulance.STATUS_CHOICES)
    status_labels = [status_label_map.get(item['status'], item['status']) for item in status_counts]
    status_data = [item['count'] for item in status_counts]

    # Trip purpose distribution (top 5 + other)
    purpose_counts = list(
        AmbulanceUsageRecord.objects.values('purpose').annotate(count=Count('id')).order_by('-count')
    )
    top_purposes = purpose_counts[:5]
    other_count = sum(item['count'] for item in purpose_counts[5:])
    purpose_labels = [item['purpose'] or 'Other' for item in top_purposes]
    purpose_data = [item['count'] for item in top_purposes]
    if other_count:
        purpose_labels.append('Other')
        purpose_data.append(other_count)
    
    # Per-ambulance breakdown
    ambulance_breakdown = Ambulance.objects.annotate(
        total_trips=Count('usage_records'),
        total_distance=Sum(F('usage_records__end_mileage') - F('usage_records__start_mileage'))
    ).order_by('-total_trips')
    
    context = {
        'monthly_stats': monthly_stats,
        'quarterly_stats': quarterly_stats,
        'ambulance_breakdown': ambulance_breakdown,
        'monthly_chart_data': json.dumps(monthly_data),
        'monthly_chart_labels': json.dumps(monthly_labels),
        'daily_chart_data': json.dumps(daily_data),
        'daily_chart_labels': json.dumps(daily_labels),
        'status_chart_data': json.dumps(status_data),
        'status_chart_labels': json.dumps(status_labels),
        'purpose_chart_data': json.dumps(purpose_data),
        'purpose_chart_labels': json.dumps(purpose_labels),
        'user_name': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'ambulance/statistics.html', context)


@login_required
def ambulance_mis_dashboard(request):
    """Ambulance MIS Admin dashboard - user and driver management for ambulance module."""
    # Check authorization
    try:
        profile = request.user.profile
        if profile.role != 'ambulance_mis' or profile.module not in ['ambulance', 'both']:
            return unauthorized_response(request, 'You do not have access to the Ambulance MIS Admin dashboard.')
    except Profile.DoesNotExist:
        return unauthorized_response(request, 'Profile not found.')
    
    # Get statistics for display
    total_users = User.objects.filter(
        profile__role__in=['ambulance_admin', 'nectacare_head', 'ambulance_mis'],
        profile__module__in=['ambulance', 'both']
    ).count()
    
    total_ambulances = Ambulance.objects.count()
    total_drivers = User.objects.filter(profile__is_dedicated_driver=True, profile__module='ambulance').count()
    
    # Recent users
    recent_users = User.objects.filter(
        profile__module__in=['ambulance', 'both']
    ).select_related('profile').order_by('-date_joined')[:10]
    
    context = {
        'total_users': total_users,
        'total_ambulances': total_ambulances,
        'total_drivers': total_drivers,
        'recent_users': recent_users,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'ambulance/mis_dashboard.html', context)


@login_required
def ambulance_mis_manage_users(request):
    """Manage ambulance module users."""
    try:
        profile = request.user.profile
        if profile.role != 'ambulance_mis':
            return unauthorized_response(request, 'Access denied.')
    except Profile.DoesNotExist:
        return unauthorized_response(request, 'Profile not found.')
    
    # Get all ambulance module users (excluding drivers)
    users = User.objects.filter(
        profile__module__in=['ambulance', 'both']
    ).exclude(
        profile__role='driver'
    ).select_related('profile').order_by('username')
    
    context = {
        'users': users,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'ambulance/mis_manage_users.html', context)


@login_required
def ambulance_mis_add_user(request):
    """Add a new ambulance module user."""
    try:
        profile = request.user.profile
        if profile.role != 'ambulance_mis':
            return unauthorized_response(request, 'Access denied.')
    except Profile.DoesNotExist:
        return unauthorized_response(request, 'Profile not found.')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        role = request.POST.get('role')
        module = request.POST.get('module', 'ambulance')
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create profile
            Profile.objects.create(
                user=user,
                role=role,
                module=module,
                subsidiary='nectacare'
            )
            
            messages.success(request, f'User {username} created successfully!')
            return redirect('fleet:ambulance_mis_manage_users')
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')
    
    context = {
        'user_name': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'ambulance/mis_add_user.html', context)


@login_required
def ambulance_mis_reset_password(request, user_id):
    """Reset password for an ambulance module user."""
    try:
        profile = request.user.profile
        if profile.role != 'ambulance_mis':
            return unauthorized_response(request, 'Access denied.')
    except Profile.DoesNotExist:
        return unauthorized_response(request, 'Profile not found.')
    
    try:
        target_user = User.objects.get(id=user_id, profile__module__in=['ambulance', 'both'])
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('fleet:ambulance_mis_manage_users')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        elif len(new_password) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
        else:
            target_user.set_password(new_password)
            target_user.save()
            messages.success(request, f'Password reset successfully for {target_user.username}!')
            return redirect('fleet:ambulance_mis_manage_users')
    
    context = {
        'target_user': target_user,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'ambulance/mis_reset_password.html', context)


@login_required
def ambulance_mis_edit_user(request, user_id):
    """Edit an existing ambulance module user."""
    try:
        profile = request.user.profile
        if profile.role != 'ambulance_mis':
            return unauthorized_response(request, 'Access denied.')
    except Profile.DoesNotExist:
        return unauthorized_response(request, 'Profile not found.')
    
    try:
        user = User.objects.get(id=user_id, profile__module__in=['ambulance', 'both'])
        user_profile = user.profile
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('fleet:ambulance_mis_manage_users')
    
    if request.method == 'POST':
        # Handle user info update
        new_username = (request.POST.get('username') or '').strip()
        if not new_username:
            messages.error(request, 'Username is required.')
            return redirect('fleet:ambulance_mis_edit_user', user_id=user.id)
        if new_username != user.username and User.objects.filter(username=new_username).exists():
            messages.error(request, 'Username is already taken.')
            return redirect('fleet:ambulance_mis_edit_user', user_id=user.id)

        user.username = new_username
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()
        
        # Handle profile update
        user_profile.role = request.POST.get('role')
        user_profile.module = request.POST.get('module', 'ambulance')
        user_profile.save()
        
        messages.success(request, f'User {user.username} updated successfully!')
        return redirect('fleet:ambulance_mis_manage_users')
    
    context = {
        'edit_user': user,
        'profile': user_profile,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'ambulance/mis_edit_user.html', context)


@login_required
def ambulance_mis_manage_drivers(request):
    """Manage ambulance drivers."""
    try:
        profile = request.user.profile
        if profile.role != 'ambulance_mis':
            return unauthorized_response(request, 'Access denied.')
    except Profile.DoesNotExist:
        return unauthorized_response(request, 'Profile not found.')
    
    # Get all drivers (users with is_dedicated_driver=True in ambulance module)
    drivers = User.objects.filter(
        profile__is_dedicated_driver=True,
        profile__module__in=['ambulance', 'both']
    ).select_related('profile').order_by('first_name', 'last_name', 'username')
    
    context = {
        'drivers': drivers,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'ambulance/mis_manage_drivers.html', context)


@login_required
def ambulance_mis_add_driver(request):
    """Add a new ambulance driver."""
    try:
        profile = request.user.profile
        if profile.role != 'ambulance_mis':
            return unauthorized_response(request, 'Access denied.')
    except Profile.DoesNotExist:
        return unauthorized_response(request, 'Profile not found.')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        try:
            # Auto-generate a unique username since drivers do not log in
            base = f"amb_driver_{first_name}_{last_name}".strip("_").lower()
            base = re.sub(r"[^a-z0-9]+", "_", base) or "amb_driver"
            username = base
            counter = 1
            while User.objects.filter(username=username).exists():
                counter += 1
                username = f"{base}_{counter}"

            # Create user with an unusable password
            user = User.objects.create_user(
                username=username,
                email=email,
                password=None,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create profile as driver
            Profile.objects.create(
                user=user,
                role='driver',
                module='ambulance',
                subsidiary='nectacare',
                is_dedicated_driver=True
            )
            
            messages.success(request, f'Driver {username} created successfully!')
            return redirect('fleet:ambulance_mis_manage_drivers')
        except Exception as e:
            messages.error(request, f'Error creating driver: {str(e)}')
    
    context = {
        'user_name': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'ambulance/mis_add_driver.html', context)


@login_required
def ambulance_mis_view_logs(request):
    """View system logs for ambulance module."""
    try:
        profile = request.user.profile
        if profile.role != 'ambulance_mis':
            return unauthorized_response(request, 'Access denied.')
    except Profile.DoesNotExist:
        return unauthorized_response(request, 'Profile not found.')
    
    # Get recent ambulance-related activities
    recent_ambulances = Ambulance.objects.all().order_by('-created_at')[:20]
    recent_usage = AmbulanceUsageRecord.objects.all().select_related('ambulance', 'driver').order_by('-usage_date')[:20]
    recent_service = AmbulanceServiceRecord.objects.all().select_related('ambulance').order_by('-service_date')[:20]
    recent_users = User.objects.filter(
        profile__module__in=['ambulance', 'both']
    ).select_related('profile').order_by('-date_joined')[:20]
    
    context = {
        'recent_ambulances': recent_ambulances,
        'recent_usage': recent_usage,
        'recent_service': recent_service,
        'recent_users': recent_users,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'ambulance/mis_view_logs.html', context)


@login_required
def ambulance_handover_checklist(request):
    """View active ambulance trips and submit handover checklists."""
    try:
        profile = request.user.profile
        if profile.role != 'ambulance_admin':
            return unauthorized_response(request, 'Access denied.')
    except Profile.DoesNotExist:
        return unauthorized_response(request, 'Profile not found.')
    
    # Get active trips (no end_mileage yet)
    active_trips = AmbulanceUsageRecord.objects.filter(
        end_mileage__isnull=True
    ).select_related('ambulance', 'driver').order_by('-created_at')
    
    # Get trips with handover status
    trips_with_handovers = []
    for trip in active_trips:
        has_handover = hasattr(trip, 'handover')
        handover_status = trip.handover.approval_status if has_handover else None
        
        trips_with_handovers.append({
            'trip': trip,
            'has_handover': has_handover,
            'handover_status': handover_status,
            'can_submit': not has_handover or handover_status == 'rejected',
        })

    previous_handovers = AmbulanceHandoverChecklist.objects.select_related(
        'ambulance',
        'driver',
        'usage_record'
    ).order_by('-submitted_at')
    
    context = {
        'trips_with_handovers': trips_with_handovers,
        'previous_handovers': previous_handovers,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'ambulance/handover_checklist.html', context)


@login_required
def ambulance_handover_detail(request, trip_id):
    """Submit handover checklist for a specific trip."""
    try:
        profile = request.user.profile
        if profile.role != 'ambulance_admin':
            return unauthorized_response(request, 'Access denied.')
    except Profile.DoesNotExist:
        return unauthorized_response(request, 'Profile not found.')
    
    trip = get_object_or_404(AmbulanceUsageRecord, id=trip_id)
    
    if request.method == 'POST':
        try:
            return_mileage = request.POST.get('return_mileage', '').strip()
            fuel_level = request.POST.get('fuel_level', '').strip()

            # Validate return_mileage
            if not return_mileage:
                messages.error(request, 'Return mileage is required.')
                return redirect('fleet:ambulance_handover_detail', trip_id=trip.id)
            
            try:
                return_mileage = int(return_mileage)
                if return_mileage < 0:
                    messages.error(request, 'Return mileage must be a positive number.')
                    return redirect('fleet:ambulance_handover_detail', trip_id=trip.id)
            except (ValueError, TypeError):
                messages.error(request, 'Return mileage must be a valid number.')
                return redirect('fleet:ambulance_handover_detail', trip_id=trip.id)

            # Validate fuel_level
            if not fuel_level:
                messages.error(request, 'Fuel level is required.')
                return redirect('fleet:ambulance_handover_detail', trip_id=trip.id)

            # Create or update handover checklist
            handover, created = AmbulanceHandoverChecklist.objects.get_or_create(
                usage_record=trip,
                defaults={
                    'ambulance': trip.ambulance,
                    'driver': trip.driver,
                    'return_mileage': return_mileage,
                    'fuel_level': fuel_level,
                }
            )
            
            # Update fields (in case record already exists)
            handover.return_mileage = return_mileage
            handover.fuel_level = fuel_level
            handover.condition_notes = request.POST.get('condition_notes', '')
            
            # Vehicle checklist
            handover.alarm_system_functional = request.POST.get('alarm_system_functional')
            handover.alarm_system_comments = request.POST.get('alarm_system_comments', '')
            handover.lock_nuts_spanner = request.POST.get('lock_nuts_spanner')
            handover.lock_nuts_spanner_comments = request.POST.get('lock_nuts_spanner_comments', '')
            handover.spare_wheel_hatchet = request.POST.get('spare_wheel_hatchet')
            handover.spare_wheel_hatchet_comments = request.POST.get('spare_wheel_hatchet_comments', '')
            handover.seat_belts_functioning = request.POST.get('seat_belts_functioning')
            handover.seat_belts_comments = request.POST.get('seat_belts_comments', '')
            handover.hand_brake_functioning = request.POST.get('hand_brake_functioning')
            handover.hand_brake_comments = request.POST.get('hand_brake_comments', '')
            handover.view_mirrors_functioning = request.POST.get('view_mirrors_functioning')
            handover.view_mirrors_comments = request.POST.get('view_mirrors_comments', '')
            handover.vehicle_insurance_disk = request.POST.get('vehicle_insurance_disk')
            handover.vehicle_insurance_comments = request.POST.get('vehicle_insurance_comments', '')
            handover.aa_zimbabwe_card = request.POST.get('aa_zimbabwe_card')
            handover.aa_zimbabwe_comments = request.POST.get('aa_zimbabwe_comments', '')
            handover.vehicle_licence_disk = request.POST.get('vehicle_licence_disk')
            handover.vehicle_licence_comments = request.POST.get('vehicle_licence_comments', '')
            handover.lights_sirens_functional = request.POST.get('lights_sirens_functional')
            handover.lights_sirens_comments = request.POST.get('lights_sirens_comments', '')
            handover.brake_lights_functioning = request.POST.get('brake_lights_functioning')
            handover.brake_lights_comments = request.POST.get('brake_lights_comments', '')
            handover.indicators_functioning = request.POST.get('indicators_functioning')
            handover.indicators_comments = request.POST.get('indicators_comments', '')
            handover.park_lights_functioning = request.POST.get('park_lights_functioning')
            handover.park_lights_comments = request.POST.get('park_lights_comments', '')
            handover.communication_radio = request.POST.get('communication_radio')
            handover.communication_radio_comments = request.POST.get('communication_radio_comments', '')
            handover.spare_wheel = request.POST.get('spare_wheel')
            handover.spare_wheel_comments = request.POST.get('spare_wheel_comments', '')
            handover.jack_tools = request.POST.get('jack_tools')
            handover.jack_tools_comments = request.POST.get('jack_tools_comments', '')
            handover.wheel_spanner = request.POST.get('wheel_spanner')
            handover.wheel_spanner_comments = request.POST.get('wheel_spanner_comments', '')
            handover.tool_box = request.POST.get('tool_box')
            handover.tool_box_comments = request.POST.get('tool_box_comments', '')
            handover.wheel_covers = request.POST.get('wheel_covers')
            handover.wheel_covers_comments = request.POST.get('wheel_covers_comments', '')
            handover.seat_covers = request.POST.get('seat_covers')
            handover.seat_covers_comments = request.POST.get('seat_covers_comments', '')
            handover.fire_extinguisher = request.POST.get('fire_extinguisher')
            handover.fire_extinguisher_comments = request.POST.get('fire_extinguisher_comments', '')
            handover.reflectors_installed = request.POST.get('reflectors_installed')
            handover.reflectors_comments = request.POST.get('reflectors_comments', '')
            handover.car_radio = request.POST.get('car_radio')
            handover.car_radio_comments = request.POST.get('car_radio_comments', '')
            handover.floor_mats = request.POST.get('floor_mats')
            handover.floor_mats_comments = request.POST.get('floor_mats_comments', '')
            
            # Cleanliness
            handover.interior_cleanliness = request.POST.get('interior_cleanliness')
            handover.interior_cleanliness_comments = request.POST.get('interior_cleanliness_comments', '')
            handover.sanitization_completed = request.POST.get('sanitization_completed')
            handover.sanitization_comments = request.POST.get('sanitization_comments', '')
            
            # Damages
            handover.damages = request.POST.get('damages', '')
            handover.scratches_dents = request.POST.get('scratches_dents', '')
            handover.additional_comments = request.POST.get('additional_comments', '')
            
            # Files
            if request.FILES.get('checklist_document'):
                handover.checklist_document = request.FILES['checklist_document']
            if request.FILES.get('photo1'):
                handover.photo1 = request.FILES['photo1']
            if request.FILES.get('photo2'):
                handover.photo2 = request.FILES['photo2']
            if request.FILES.get('photo3'):
                handover.photo3 = request.FILES['photo3']
            
            # Reset approval status if resubmitting
            if not created:
                handover.approval_status = 'pending'
            
            handover.save()
            
            # Update usage record with closing mileage
            trip.end_mileage = handover.return_mileage
            trip.save()
            
            # Update ambulance mileage and status
            trip.ambulance.current_mileage = handover.return_mileage
            trip.ambulance.status = 'available'
            trip.ambulance.save()
            
            messages.success(request, 'Handover checklist submitted successfully!')
            return redirect('fleet:ambulance_handover_checklist')
        except Exception as e:
            messages.error(request, f'Error submitting handover: {str(e)}')
    
    context = {
        'trip': trip,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'ambulance/handover_detail.html', context)


@login_required
def ambulance_service_schedule(request):
    """View and manage ambulance service schedule."""
    try:
        profile = request.user.profile
        if profile.role not in ['ambulance_admin', 'ambulance_mis']:
            return unauthorized_response(request, 'Access denied.')
    except Profile.DoesNotExist:
        return unauthorized_response(request, 'Profile not found.')
    
    if request.method == 'POST':
        # Handle service record submission
        ambulance_id = request.POST.get('ambulance_id')
        service_date = request.POST.get('service_date')
        service_type = request.POST.get('service_type')
        service_company = request.POST.get('service_company')
        mileage_at_service = request.POST.get('mileage_at_service')
        cost = request.POST.get('cost')
        description = request.POST.get('description')
        next_service_due = request.POST.get('next_service_due')
        invoice_number = request.POST.get('invoice_number')
        
        try:
            ambulance = Ambulance.objects.get(id=ambulance_id)
            
            service_record = AmbulanceServiceRecord.objects.create(
                ambulance=ambulance,
                service_date=service_date,
                service_type=service_type,
                service_company=service_company,
                mileage_at_service=mileage_at_service,
                cost=cost if cost else None,
                description=description,
                next_service_due=next_service_due if next_service_due else None,
                invoice_number=invoice_number,
                performed_by=request.user
            )
            
            # Handle receipt upload
            if request.FILES.get('receipt'):
                service_record.receipt = request.FILES['receipt']
                service_record.save()
            
            messages.success(request, f'Service record added successfully for {ambulance.reg_number}!')
            return redirect('fleet:ambulance_service_schedule')
        except Exception as e:
            messages.error(request, f'Error adding service record: {str(e)}')
    
    # Get all ambulances with their service status
    ambulances = Ambulance.objects.all().order_by('reg_number')
    
    # Get all service records
    service_records = AmbulanceServiceRecord.objects.all().select_related('ambulance', 'performed_by').order_by('-service_date')
    
    # Calculate service due status for each ambulance
    ambulances_with_service = []
    for ambulance in ambulances:
        latest_service = ambulance.service_records.first()
        km_to_service = ambulance.km_to_service
        is_overdue = ambulance.is_service_due
        
        ambulances_with_service.append({
            'ambulance': ambulance,
            'latest_service': latest_service,
            'km_to_service': km_to_service,
            'is_overdue': is_overdue,
        })
    
    context = {
        'ambulances': ambulances,
        'ambulances_with_service': ambulances_with_service,
        'service_records': service_records[:50],  # Latest 50 records
        'user_name': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'ambulance/service_schedule.html', context)
