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
ids = [r.id for r in found]
if ids:
    found.delete()
    print('Deleted requests:', ids)
else:
    print('No matching test requests found.')
