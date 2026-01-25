"""Helper function for MIS access control."""
from django.shortcuts import redirect


def check_mis_access(request):
    """
    Check if user has MIS role. If not, redirect them to their appropriate dashboard.
    Returns None if access is allowed, or a redirect response if access denied.
    """
    if not hasattr(request.user, 'profile'):
        return redirect('fleet:login_page')
    
    if request.user.profile.role != 'mis':
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
            else:
                return redirect('fleet:login_page')
        elif role == 'ceo':
            return redirect('fleet:ceo_dashboard')
        else:
            return redirect('fleet:login_page')
    
    return None  # Access allowed
