"""
Create Ambulance MIS Admin user
Run: python create_ambulance_mis_admin.py
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poolcar.settings')
django.setup()

from django.contrib.auth.models import User
from fleet.models import Profile

def create_ambulance_mis_admin():
    """Create Ambulance MIS Admin user."""
    
    print("=" * 60)
    print("Creating Ambulance MIS Admin User")
    print("=" * 60)
    
    username = 'ambulance+mis'
    password = 'Mis1234'
    
    try:
        # Check if user exists
        if User.objects.filter(username=username).exists():
            print(f"\n⚠️  User '{username}' already exists.")
            user = User.objects.get(username=username)
            
            # Update password
            user.set_password(password)
            user.email = 'mis@nectacare.co.zw'
            user.first_name = 'MIS'
            user.last_name = 'Admin'
            user.save()
            
            # Update or create profile
            profile, created = Profile.objects.get_or_create(user=user)
            profile.role = 'ambulance_mis'
            profile.module = 'ambulance'
            profile.subsidiary = 'nectacare'
            profile.save()
            
            print(f"   ✅ User '{username}' updated successfully!")
        else:
            # Create new user
            user = User.objects.create_user(
                username=username,
                email='mis@nectacare.co.zw',
                password=password,
                first_name='MIS',
                last_name='Admin'
            )
            
            Profile.objects.create(
                user=user,
                role='ambulance_mis',
                module='ambulance',
                subsidiary='nectacare'
            )
            
            print(f"\n   ✅ User '{username}' created successfully!")
        
        print("\n" + "=" * 60)
        print("Ambulance MIS Admin Details:")
        print("=" * 60)
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   Email: mis@nectacare.co.zw")
        print(f"   Role: Ambulance MIS Admin")
        print(f"   Module: Ambulance")
        print("\n   Login URL: http://localhost:8000/ambulance/login/")
        print("\n✅ You can now login with these credentials!\n")
        
    except Exception as e:
        print(f"\n   ❌ Error: {e}")

if __name__ == '__main__':
    create_ambulance_mis_admin()
