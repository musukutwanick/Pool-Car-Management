"""
Update ambulance_admin password to 'admin' and create MIS Admin for ambulances
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poolcar.settings')
django.setup()

from django.contrib.auth.models import User
from fleet.models import Profile

print("=" * 60)
print("Updating Ambulance Passwords and Creating MIS Admin")
print("=" * 60)

# 1. Update ambulance_admin password to "admin"
print("\n1. Updating ambulance_admin password...")
try:
    user = User.objects.get(username='ambulance_admin')
    user.set_password('admin')
    user.save()
    print("   ✅ Password changed!")
    print("      Username: ambulance_admin")
    print("      New Password: admin")
except User.DoesNotExist:
    print("   ⚠️  User 'ambulance_admin' not found")

# 2. Update nectacare_head password to "admin" as well
print("\n2. Updating nectacare_head password...")
try:
    user = User.objects.get(username='nectacare_head')
    user.set_password('admin')
    user.save()
    print("   ✅ Password changed!")
    print("      Username: nectacare_head")
    print("      New Password: admin")
except User.DoesNotExist:
    print("   ⚠️  User 'nectacare_head' not found")

# 3. Create Ambulance MIS Admin
print("\n3. Creating Ambulance MIS Admin...")
try:
    if User.objects.filter(username='ambulance_mis').exists():
        print("   ⚠️  User 'ambulance_mis' already exists. Skipping.")
    else:
        mis_user = User.objects.create_user(
            username='ambulance_mis',
            email='mis@nectacare.co.zw',
            password='admin',
            first_name='MIS',
            last_name='Ambulance'
        )
        
        Profile.objects.create(
            user=mis_user,
            role='ambulance_mis',
            module='ambulance',
            subsidiary='nectacare'
        )
        
        print("   ✅ Ambulance MIS Admin created successfully!")
        print("      Username: ambulance_mis")
        print("      Password: admin")
        print("      Email: mis@nectacare.co.zw")
except Exception as e:
    print(f"   ❌ Error creating MIS Admin: {e}")

print("\n" + "=" * 60)
print("Update Complete!")
print("=" * 60)
print("\n🔐 Updated Ambulance Login Credentials:")
print("   1. Ambulance Admin - ambulance_admin / admin")
print("   2. Nectacare Head - nectacare_head / admin")
print("   3. Ambulance MIS - ambulance_mis / admin")
print("\n✅ All passwords are now: admin\n")
