"""
Management command to clear all service records from the database.
Usage: python manage.py clear_service_records
"""

from django.core.management.base import BaseCommand
from fleet.models import ServiceRecord


class Command(BaseCommand):
    help = 'Clear all service records from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion without prompting',
        )

    def handle(self, *args, **options):
        # Count existing records
        count = ServiceRecord.objects.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No service records found in the database.'))
            return
        
        # Confirm deletion
        if not options['confirm']:
            self.stdout.write(self.style.WARNING(f'Found {count} service record(s) in the database.'))
            response = input('Are you sure you want to delete ALL service records? (yes/no): ')
            if response.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Operation cancelled.'))
                return
        
        # Delete all records
        ServiceRecord.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} service record(s).'))
