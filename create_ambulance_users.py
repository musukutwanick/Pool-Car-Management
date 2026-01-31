"""
Create test users for Ambulance Manager module
Run: python create_ambulance_users.py
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poolcar.settings')
django.setup()

from django.contrib.auth.models import User
from fleet.models import Profile

def create_ambulance_users():
    """Create test users for Ambulance Manager."""
    
    print("=" * 60)
    print("Creating Ambulance Manager Test Users")
    print("=" * 60)
    
    # 1. Create Ambulance Admin
    print("\n1. Creating Ambulance Admin...")
    try:
        # Check if user exists
        if User.objects.filter(username='ambulance_admin').exists():
            print("   ⚠️  User 'ambulance_admin' already exists. Skipping.")
        else:
            admin_user = User.objects.create_user(
                username='ambulance_admin',
                email='ambulance@nectacare.co.zw',
                password='admin123',
                first_name='John',
                last_name='Medic'
            )
            
            Profile.objects.create(
                user=admin_user,
                role='ambulance_admin',
                module='ambulance',
                subsidiary='nectacare'
            )
            
            print("   ✅ Ambulance Admin created successfully!")
            print("      Username: ambulance_admin")
            print("      Password: admin123")
            print("      Email: ambulance@nectacare.co.zw")
    except Exception as e:
        print(f"   ❌ Error creating Ambulance Admin: {e}")
    
    # 2. Create Nectacare Head
    print("\n2. Creating Nectacare Head...")
    try:
        # Check if user exists
        if User.objects.filter(username='nectacare_head').exists():
            print("   ⚠️  User 'nectacare_head' already exists. Skipping.")
        else:
            head_user = User.objects.create_user(
                username='nectacare_head',
                email='head@nectacare.co.zw',
                password='head123',
                first_name='Sarah',
                last_name='Director'
            )
            
            Profile.objects.create(
                user=head_user,
                role='nectacare_head',
                module='ambulance',
                subsidiary='nectacare'
            )
            
            print("   ✅ Nectacare Head created successfully!")
            print("      Username: nectacare_head")
            print("      Password: head123")
            print("      Email: head@nectacare.co.zw")
    except Exception as e:
        print(f"   ❌ Error creating Nectacare Head: {e}")
    
    # 3. Create Dual Access User (Optional)
    print("\n3. Creating Dual Access User (Optional)...")
    try:
        # Check if user exists
        if User.objects.filter(username='dual_access').exists():
            print("   ⚠️  User 'dual_access' already exists. Skipping.")
        else:
            dual_user = User.objects.create_user(
                username='dual_access',
                email='dual@cellinsurance.co.zw',
                password='dual123',
                first_name='Mike',
                last_name='Manager'
            )
            
            Profile.objects.create(
                user=dual_user,
                role='ambulance_admin',
                module='both',  # Has access to both modules
                subsidiary='nectacare'
            )
            
            print("   ✅ Dual Access User created successfully!")
            print("      Username: dual_access")
            print("      Password: dual123")
            print("      Email: dual@cellinsurance.co.zw")
            print("      Can access: Pool Car Manager AND Ambulance Manager")
    except Exception as e:
        print(f"   ❌ Error creating Dual Access User: {e}")
    
    print("\n" + "=" * 60)
    print("User Creation Complete!")
    print("=" * 60)
    print("\n📋 Summary:")
    print("   • Ambulance Manager Login: http://localhost:8000/ambulance/login/")
    print("   • Pool Car Manager Login: http://localhost:8000/login/")
    print("   • Landing Page: http://localhost:8000/")
    print("\n🔐 Test Credentials:")
    print("   1. Ambulance Admin - ambulance_admin / admin123")
    print("   2. Nectacare Head - nectacare_head / head123")
    print("   3. Dual Access - dual_access / dual123 (optional)")
    print("\n✅ You can now test the Ambulance Manager module!\n")

if __name__ == '__main__':
    create_ambulance_users()
