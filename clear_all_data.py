"""
Clear all requests, handovers, and service records
Keep: Users, Profiles, Vehicles (but reset their status to available)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poolcar.settings')
django.setup()

from django.contrib.auth.models import User
from fleet.models import CarRequest, HandoverChecklist, Vehicle, ServiceRecord

print("=== CLEARING ALL DATA ===\n")

# Count before deletion
car_requests_count = CarRequest.objects.count()
handovers_count = HandoverChecklist.objects.count()
service_records_count = ServiceRecord.objects.count()
users_count = User.objects.count()
vehicles_count = Vehicle.objects.count()

print(f"Current data:")
print(f"  - Car Requests: {car_requests_count}")
print(f"  - Handovers: {handovers_count}")
print(f"  - Service Records: {service_records_count}")
print(f"  - Users: {users_count} (WILL BE KEPT)")
print(f"  - Vehicles: {vehicles_count} (WILL BE KEPT, status reset)")

print("\n⚠️  WARNING: This will delete ALL requests, handovers, and service records!")
confirm = input("\nType 'DELETE' to confirm: ")

if confirm != 'DELETE':
    print("❌ Cancelled - no data was deleted")
    exit()

print("\n🗑️  Deleting data...")

# Delete handovers first (they reference car requests)
deleted_handovers = HandoverChecklist.objects.all().delete()
print(f"✓ Deleted {deleted_handovers[0]} handover checklists")

# Delete service records
deleted_services = ServiceRecord.objects.all().delete()
print(f"✓ Deleted {deleted_services[0]} service records")

# Delete car requests
deleted_requests = CarRequest.objects.all().delete()
print(f"✓ Deleted {deleted_requests[0]} car requests")

# Reset all vehicles to available status and clear assigned vehicles
print("\n🚗 Resetting vehicles...")
vehicles_updated = Vehicle.objects.all().update(status='available')
print(f"✓ Reset {vehicles_updated} vehicles to 'available' status")

print("\n✅ DATA CLEANUP COMPLETE!")
print(f"\nRemaining:")
print(f"  - Users: {User.objects.count()}")
print(f"  - Vehicles: {Vehicle.objects.count()} (all available)")
print(f"  - Car Requests: {CarRequest.objects.count()}")
print(f"  - Handovers: {HandoverChecklist.objects.count()}")
print(f"  - Service Records: {ServiceRecord.objects.count()}")
