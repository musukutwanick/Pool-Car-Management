"""
Create the initial MIS Admin user
Run with: python create_mis_admin.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poolcar.settings')
django.setup()

from django.contrib.auth.models import User
from fleet.models import Profile

# Create MIS admin user
username = 'MIS'
password = 'MIS123'

user, created = User.objects.get_or_create(
    username=username,
    defaults={
        'first_name': 'MIS',
        'last_name': 'Admin',
        'email': 'mis@cellinsurance.com',
        'is_staff': True
    }
)

if created or not user.has_usable_password():
    user.set_password(password)
    user.save()
    action = 'Created' if created else 'Updated password for'
    print(f"✓ {action} MIS Admin user")
else:
    print(f"✓ MIS Admin user already exists")

# Create or update profile
profile, created = Profile.objects.get_or_create(user=user)
profile.role = 'mis'
profile.save()

print(f"✓ Profile set to: MIS Administrator")
print(f"\n{'='*50}")
print(f"MIS Admin Login Credentials:")
print(f"  Username: {username}")
print(f"  Password: {password}")
print(f"{'='*50}")
print(f"\nYou can now:")
print(f"  1. Log in at http://127.0.0.1:8000/login/")
print(f"  2. Go to Manage Users")
print(f"  3. Add all employees, GMs, CEO, and Admin")
