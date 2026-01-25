import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poolcar.settings')
django.setup()
from fleet.models import Vehicle

v = Vehicle.objects.filter(id=1).first()
print('FOUND:', bool(v))
if not v:
    print('No vehicle with id=1')
else:
    img = getattr(v, 'image', None)
    print('image.name ->', getattr(img, 'name', None))
    try:
        print('image.url ->', img.url)
    except Exception as e:
        print('image.url error ->', e)
    try:
        print('image.path ->', img.path)
        print('exists ->', os.path.exists(img.path))
    except Exception as e:
        print('image.path error ->', e)
