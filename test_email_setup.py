"""
Test script to verify email notification system is working.
Run with: python manage.py shell < test_email_setup.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poolcar.settings')
django.setup()

from fleet.models import CarRequest, Profile
from django.contrib.auth.models import User
from django.db.models.signals import post_save

print("\n=== Email Notification System Test ===\n")

# 1. Check signal registration
print("1. Checking signal registration...")
receivers = post_save.receivers
car_request_receivers = [r for r in receivers if 'CarRequest' in str(r)]
if car_request_receivers:
    print("   ✓ Signals registered for CarRequest")
else:
    print("   ✗ No signals found for CarRequest")

# 2. Check email configuration
from django.conf import settings
print("\n2. Checking email configuration...")
print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"   EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not configured')}")
print(f"   EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not configured')}")
print(f"   DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not configured')}")

if 'console' in settings.EMAIL_BACKEND:
    print("   ✓ Using console backend (emails will print to terminal)")
elif 'smtp' in settings.EMAIL_BACKEND:
    print("   ✓ Using SMTP backend (emails will be sent)")
    if not getattr(settings, 'EMAIL_HOST_USER', None):
        print("   ⚠ Warning: EMAIL_HOST_USER not configured")
else:
    print(f"   ⚠ Unknown backend: {settings.EMAIL_BACKEND}")

# 3. Check user email addresses
print("\n3. Checking user email configuration...")

gm_profiles = Profile.objects.filter(role='gm').select_related('user')
print(f"   GMs configured: {gm_profiles.count()}")
for profile in gm_profiles:
    email_status = "✓" if profile.user.email else "✗ No email"
    print(f"     - {profile.user.username} ({profile.get_subsidiary_display()}): {email_status}")

ceo_profiles = Profile.objects.filter(role='ceo').select_related('user')
print(f"   CEOs configured: {ceo_profiles.count()}")
for profile in ceo_profiles:
    email_status = "✓" if profile.user.email else "✗ No email"
    print(f"     - {profile.user.username}: {email_status}")

admin_profiles = Profile.objects.filter(role='admin').select_related('user')
print(f"   Admins configured: {admin_profiles.count()}")
for profile in admin_profiles:
    email_status = "✓" if profile.user.email else "✗ No email"
    print(f"     - {profile.user.username}: {email_status}")

# 4. Check recent requests
print("\n4. Recent requests status...")
recent = CarRequest.objects.order_by('-created_at')[:5]
if recent:
    for req in recent:
        print(f"   Request #{req.request_code}:")
        print(f"     Status: {req.status}")
        print(f"     GM Approved: {'Yes' if req.approver1 else 'No'}")
        print(f"     CEO Approved: {'Yes' if req.approver2 else 'No'}")
        print(f"     Vehicle Assigned: {'Yes' if req.assigned_vehicle else 'No'}")
else:
    print("   No requests found")

print("\n=== Test Complete ===")
print("\nTo test email notifications:")
print("1. Ensure users have valid email addresses")
print("2. Submit a new vehicle request as an employee")
print("3. Check terminal output for email (console backend) or inbox (SMTP)")
print("4. Approve as GM → check for CEO notification (out-of-town) or admin/employee notification")
print("5. Assign vehicle as admin → check employee receives assignment email")
print("\n")
