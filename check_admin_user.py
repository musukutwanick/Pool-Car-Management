import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poolcar.settings')
django.setup()

from django.contrib.auth.models import User
from fleet.models import Profile

# Find admin users
admin_users = User.objects.filter(is_staff=True)
print(f"\nFound {admin_users.count()} admin users:\n")

for u in admin_users:
    print(f"Username: {u.username}")
    print(f"First name: '{u.first_name}'")
    print(f"Last name: '{u.last_name}'")
    print(f"Full name: '{u.get_full_name()}'")
    try:
        p = u.profile
        print(f"Profile role: {p.role} ({p.get_role_display()})")
        print(f"Profile subsidiary: {p.subsidiary}")
    except Profile.DoesNotExist:
        print("No profile")
    print("-" * 50)
