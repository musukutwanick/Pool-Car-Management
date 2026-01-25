"""
Send one test email via Django to verify SMTP authentication using current .env credentials.
Run: .venv\Scripts\python.exe send_test_smtp.py
"""
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poolcar.settings')
django.setup()

from django.core.mail import send_mail

TO = ['nmusukutwa@cellinsurance.co.zw']  # send to yourself to confirm
SUBJECT = 'SMTP Live Test'
BODY = 'This is a test email sent from the Pool Car Management app to verify SMTP auth.'
FROM = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)

print('Using EMAIL_BACKEND =', settings.EMAIL_BACKEND)
print('Using EMAIL_HOST =', settings.EMAIL_HOST)
print('Using FROM =', FROM)

try:
    result = send_mail(SUBJECT, BODY, FROM, TO, fail_silently=False)
    print('send_mail returned:', result)
    print('If no exception, email was handed to SMTP client successfully.')
except Exception as e:
    print('Error sending email:')
    import traceback
    traceback.print_exc()
    raise
