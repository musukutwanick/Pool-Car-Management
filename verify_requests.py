#!/usr/bin/env python
"""Verify approval requests are set up correctly."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poolcar.settings')
django.setup()

from fleet.models import CarRequest

print('All CarRequests:')
print('ID | Status      | Out  | Subsidiary      | Purpose')
print('-' * 90)
for r in CarRequest.objects.all().order_by('-created_at'):
    print(f'{r.id:2d} | {r.status:11s} | {str(r.out_of_town)[0]:4s} | {r.subsidiary:15s} | {r.purpose[:40]}')

print('\n' + '='*90)
print('APPROVAL COUNTS:')
print('='*90)
print(f'CEO approvals (out_of_town=True, status=pending): {CarRequest.objects.filter(status="pending", out_of_town=True).count()}')
print(f'GM Cell Insurance approvals: {CarRequest.objects.filter(status="pending", out_of_town=False, subsidiary="cell_insurance").count()}')
print(f'GM Cellmed approvals: {CarRequest.objects.filter(status="pending", out_of_town=False, subsidiary="cellmed").count()}')
print(f'GM Nectacare approvals: {CarRequest.objects.filter(status="pending", out_of_town=False, subsidiary="nectacare").count()}')
