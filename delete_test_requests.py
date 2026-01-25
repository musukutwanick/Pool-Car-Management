import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poolcar.settings')
django.setup()

from fleet.models import CarRequest

PURPOSES = [
    'Business trip to Bulawayo for client presentation',
    'Client meeting in Harare CBD',
    'Cellmed office visit and equipment pickup',
    'Nectacare facility inspection'
]

found = CarRequest.objects.filter(purpose__in=PURPOSES)
if not found.exists():
    print('No matching test requests found.')
else:
    print(f'Found {found.count()} test requests:')
    for r in found:
        print(f' - id={r.id}, purpose="{r.purpose}", requester={r.requester.username if r.requester else "<none>"}, status={r.status}')
    ids = [r.id for r in found]
    confirm = input(f"Delete these {len(ids)} requests? Type 'yes' to confirm: ")
    if confirm.lower() == 'yes':
        found.delete()
        print(f'Deleted requests: {ids}')
    else:
        print('Aborted. No changes made.')
