"""
Script to create test users for the Pool Car Management system.
Run with: python setup_users.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poolcar.settings')
django.setup()

from django.contrib.auth.models import User
from fleet.models import Profile

def create_user_with_profile(username, password, first_name, last_name, role, subsidiary=None):
    """Create or update a user and their profile."""
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': first_name,
            'last_name': last_name,
        }
    )
    
    if created or not user.has_usable_password():
        user.set_password(password)
        user.save()
        print(f"{'Created' if created else 'Updated password for'} user: {username}")
    else:
        print(f"User already exists: {username}")
    
    # Create or update profile
    profile, created = Profile.objects.get_or_create(user=user)
    profile.role = role
    if subsidiary:
        profile.subsidiary = subsidiary
    profile.save()
    print(f"  Profile: {role}" + (f" ({subsidiary})" if subsidiary else ""))
    
    return user

print("Setting up users for Pool Car Management System...\n")

# Create employee users
create_user_with_profile('nick', 'nick123', 'Nick', 'Employee', 'employee')

# Create admin user
create_user_with_profile('admin', 'admin123', 'Admin', 'User', 'admin')

# Create GM users for each subsidiary
create_user_with_profile('CellinsureGM', 'Cellinsure123', 'Cell Insurance', 'GM', 'gm', 'cell_insurance')
create_user_with_profile('CellGM', 'CellmedGM123', 'Cellmed', 'GM', 'gm', 'cellmed')
create_user_with_profile('Necta', 'Necta123', 'Nectacare', 'GM', 'gm', 'nectacare')

# Create CEO user
create_user_with_profile('CEO', 'CEO123', 'Chief Executive', 'Officer', 'ceo')

# Create MIS user
create_user_with_profile('MIS', 'MIS123', 'MIS', 'Admin', 'mis')

print("\n✓ All users created successfully!")
print("\nYou can now log in with any of these accounts:")
print("  - nick / nick123 (Employee)")
print("  - admin / admin123 (Admin)")
print("  - CellinsureGM / Cellinsure123 (GM - Cell Insurance)")
print("  - CellGM / CellmedGM123 (GM - Cellmed)")
print("  - Necta / Necta123 (GM - Nectacare)")
print("  - CEO / CEO123 (CEO)")
print("  - MIS / MIS123 (MIS)")
