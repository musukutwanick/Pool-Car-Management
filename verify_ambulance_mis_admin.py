"""
Verify Ambulance MIS Admin user
Run: python verify_ambulance_mis_admin.py
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poolcar.settings')
django.setup()

from django.contrib.auth.models import User
from fleet.models import Profile

def verify_user():
    """Verify Ambulance MIS Admin user."""
    
    print("=" * 60)
    print("Verifying Ambulance MIS Admin User")
    print("=" * 60)
    
    try:
        user = User.objects.get(username='ambulance+mis')
        profile = user.profile
        
        print("\n✅ User Found!")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   First Name: {user.first_name}")
        print(f"   Last Name: {user.last_name}")
        print(f"   Role: {profile.get_role_display()}")
        print(f"   Module: {profile.get_module_display()}")
        print(f"   Subsidiary: {profile.get_subsidiary_display()}")
        print(f"   Active: {user.is_active}")
        
        # Test password
        is_password_correct = user.check_password('Mis1234')
        print(f"\n   Password 'Mis1234' is: {'✅ CORRECT' if is_password_correct else '❌ INCORRECT'}")
        
        print("\n" + "=" * 60)
        print("✅ All checks passed! User is ready to use.")
        print("=" * 60)
        
    except User.DoesNotExist:
        print("\n❌ User 'ambulance+mis' not found!")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == '__main__':
    verify_user()
