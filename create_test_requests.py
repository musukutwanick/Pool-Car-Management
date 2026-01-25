#!/usr/bin/env python
"""Create test requests for GM and CEO approval testing."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poolcar.settings')
django.setup()

from django.contrib.auth import get_user_model
from fleet.models import CarRequest, Profile
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

# Find or create an employee user
employee_user = User.objects.filter(profile__role='employee').first()
if not employee_user:
    print('No employee user found, creating one...')
    employee_user = User.objects.create_user(
        username='testemployee',
        password='pass123',
        first_name='Test',
        last_name='Employee',
        email='test@cellinsurance.co.zw'
    )
    Profile.objects.create(
        user=employee_user,
        role='employee',
        subsidiary='cell_insurance'
    )
    print(f'Created employee user: {employee_user.username}')
else:
    print(f'Using existing employee: {employee_user.username}')

# Create test request dates
start = timezone.now() + timedelta(days=2)
end = start + timedelta(days=5)

# Create CEO approval request (out_of_town=True)
req1 = CarRequest.objects.create(
    requester=employee_user,
    purpose='Business trip to Bulawayo for client presentation',
    start_time=start,
    end_time=end,
    location='Bulawayo',
    out_of_town=True,
    subsidiary='cell_insurance',
    status='pending'
)
print(f'✓ Created CEO request #{req1.id}: out_of_town=True, status=pending')

# Create GM approval request for Cell Insurance (out_of_town=False)
req2 = CarRequest.objects.create(
    requester=employee_user,
    purpose='Client meeting in Harare CBD',
    start_time=start,
    end_time=end,
    location='Harare CBD',
    out_of_town=False,
    subsidiary='cell_insurance',
    status='pending'
)
print(f'✓ Created GM request #{req2.id}: out_of_town=False, status=pending, subsidiary=cell_insurance')

# Create GM approval request for Cellmed (out_of_town=False)
req3 = CarRequest.objects.create(
    requester=employee_user,
    purpose='Cellmed office visit and equipment pickup',
    start_time=start,
    end_time=end,
    location='Cellmed Office',
    out_of_town=False,
    subsidiary='cellmed',
    status='pending'
)
print(f'✓ Created GM request #{req3.id}: out_of_town=False, status=pending, subsidiary=cellmed')

# Create GM approval request for Nectacare (out_of_town=False)
req4 = CarRequest.objects.create(
    requester=employee_user,
    purpose='Nectacare facility inspection',
    start_time=start,
    end_time=end,
    location='Nectacare Facility',
    out_of_town=False,
    subsidiary='nectacare',
    status='pending'
)
print(f'✓ Created GM request #{req4.id}: out_of_town=False, status=pending, subsidiary=nectacare')

print('\n✅ Test requests created successfully!')
print('\nSummary:')
print(f'  - CEO approvals (out_of_town=True): {CarRequest.objects.filter(status="pending", out_of_town=True).count()}')
print(f'  - GM Cell Insurance approvals: {CarRequest.objects.filter(status="pending", out_of_town=False, subsidiary="cell_insurance").count()}')
print(f'  - GM Cellmed approvals: {CarRequest.objects.filter(status="pending", out_of_town=False, subsidiary="cellmed").count()}')
print(f'  - GM Nectacare approvals: {CarRequest.objects.filter(status="pending", out_of_town=False, subsidiary="nectacare").count()}')
