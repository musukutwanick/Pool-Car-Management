"""
Check Brandon Ncube's handover submission status
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poolcar.settings')
django.setup()

from django.contrib.auth.models import User
from fleet.models import CarRequest, HandoverChecklist

print("=== CHECKING BRANDON NCUBE'S HANDOVER ===\n")

# Find Brandon
print("All users:")
for u in User.objects.all():
    print(f"  - {u.username} ({u.get_full_name()})")

print("\nLooking for Brandon...")
try:
    brandon = User.objects.get(username__icontains='ncube')
    print(f"✓ Found user: {brandon.username} ({brandon.get_full_name()})")
    print(f"  Email: {brandon.email}")
    if hasattr(brandon, 'profile'):
        print(f"  Role: {brandon.profile.get_role_display()}")
        print(f"  Employee Type: {brandon.profile.get_employee_type_display()}")
except User.DoesNotExist:
    print("✗ Brandon/Ncube not found - trying first name...")
    try:
        brandon = User.objects.get(first_name__icontains='brandon')
        print(f"✓ Found user: {brandon.username} ({brandon.get_full_name()})")
    except User.DoesNotExist:
        print("✗ No Brandon found")
        exit()

print("\n--- Brandon's Car Requests ---")
requests = CarRequest.objects.filter(requester=brandon).order_by('-created_at')
print(f"Total requests: {requests.count()}\n")

for req in requests[:5]:  # Show last 5
    print(f"Request #{req.id} ({req.request_code}):")
    print(f"  Status: {req.status}")
    print(f"  Vehicle: {req.assigned_vehicle.reg_number if req.assigned_vehicle else 'None'}")
    print(f"  Created: {req.created_at}")
    
    # Check for handover
    try:
        handover = HandoverChecklist.objects.get(request=req)
        print(f"  ✓ Handover exists:")
        print(f"    - Approval Status: {handover.approval_status}")
        print(f"    - Submitted At: {handover.submitted_at}")
        print(f"    - Reviewed By: {handover.reviewed_by}")
        print(f"    - Reviewed At: {handover.reviewed_at}")
        print(f"    - Mileage: {handover.mileage_kms}")
    except HandoverChecklist.DoesNotExist:
        print(f"  ✗ No handover checklist")
    print()

print("\n--- All Unreviewed Handovers (Admin Query) ---")
unreviewed = HandoverChecklist.objects.filter(
    reviewed_by__isnull=True
).select_related('request', 'request__requester')

print(f"Total unreviewed: {unreviewed.count()}\n")
for h in unreviewed[:10]:
    print(f"Request #{h.request.id} - {h.request.requester.username}")
    print(f"  Submitted: {h.submitted_at}")
    print(f"  Status: {h.approval_status}")
    print(f"  Request Status: {h.request.status}")
    print()
