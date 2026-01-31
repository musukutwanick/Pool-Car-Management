#!/usr/bin/env python
"""
Clear ServiceRecord table data
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poolcar.settings')
django.setup()

from fleet.models import ServiceRecord

# Count before deletion
count_before = ServiceRecord.objects.count()
print(f"Records before: {count_before}")

# Delete all service records
ServiceRecord.objects.all().delete()

# Count after deletion
count_after = ServiceRecord.objects.count()
print(f"Records after: {count_after}")
print(f"✓ Deleted {count_before} service records")
