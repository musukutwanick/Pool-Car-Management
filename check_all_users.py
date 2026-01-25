import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poolcar.settings')
django.setup()

from django.contrib.auth.models import User
from fleet.models import Profile

print("\n=== ALL USERS ===")
users = User.objects.all().order_by('username')
for u in users:
    try:
        role = u.profile.get_role_display()
        sub = u.profile.get_subsidiary_display()
    except:
        role = "No profile"
        sub = "N/A"
    
    print(f"{u.username:20} | Name: {u.get_full_name():30} | Role: {role:15} | Sub: {sub}")

print("\n=== GM USERS ===")
gm_users = User.objects.filter(profile__role='gm')
for u in gm_users:
    print(f"{u.username} | {u.get_full_name()} | {u.profile.get_subsidiary_display()}")
