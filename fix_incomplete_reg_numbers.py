"""
Script to identify vehicles with incomplete registration numbers.
Run this to see which vehicles need their registration numbers updated.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poolcar.settings')
django.setup()

from fleet.models import Vehicle

def check_incomplete_reg_numbers():
    """Check for vehicles with potentially incomplete registration numbers."""
    vehicles = Vehicle.objects.all()
    
    print("\n" + "="*60)
    print("VEHICLE REGISTRATION NUMBERS CHECK")
    print("="*60 + "\n")
    
    incomplete = []
    complete = []
    
    for vehicle in vehicles:
        reg = vehicle.reg_number
        # Check if reg number has only letters (no digits)
        has_digits = any(char.isdigit() for char in reg)
        
        if not has_digits and len(reg) <= 4:
            # Likely incomplete (e.g., "AFG", "AGV")
            incomplete.append(vehicle)
            print(f"⚠️  INCOMPLETE: ID={vehicle.id:2d} | Reg: '{reg:15s}' | Model: {vehicle.model}")
        else:
            complete.append(vehicle)
            print(f"✓  COMPLETE:   ID={vehicle.id:2d} | Reg: '{reg:15s}' | Model: {vehicle.model}")
    
    print("\n" + "="*60)
    print(f"Summary: {len(complete)} complete, {len(incomplete)} incomplete")
    print("="*60 + "\n")
    
    if incomplete:
        print("ACTION REQUIRED:")
        print("Please update the following vehicles through the admin panel:")
        print("(Go to Admin Dashboard → Manage Vehicles → Edit Vehicle)")
        print()
        for v in incomplete:
            print(f"  • Vehicle ID {v.id}: Update '{v.reg_number}' to full registration")
        print()

if __name__ == '__main__':
    check_incomplete_reg_numbers()
