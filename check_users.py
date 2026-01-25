#!/usr/bin/env python
"""Check all user profiles."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poolcar.settings')
django.setup()

from django.contrib.auth import get_user_model
from fleet.models import Profile

User = get_user_model()

print('All Users:')
print('Username       | Email                    | Role      | First/Last Name')
print('-' * 85)
for u in User.objects.all():
    try:
        p = u.profile
        fullname = f'{u.first_name} {u.last_name}'.strip() or '(no name)'
        print(f'{u.username:14s} | {u.email:24s} | {p.role:9s} | {fullname}')
    except Profile.DoesNotExist:
        print(f'{u.username:14s} | {u.email:24s} | NO PROFILE')
