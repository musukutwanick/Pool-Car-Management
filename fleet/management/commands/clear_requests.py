from django.core.management.base import BaseCommand
from fleet.models import CarRequest, HandoverChecklist


class Command(BaseCommand):
    help = 'Clear all car requests and approvals from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion without prompting',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            confirm = input('This will delete ALL car requests and handovers. Type "yes" to confirm: ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return

        # Count before deletion
        request_count = CarRequest.objects.count()
        handover_count = HandoverChecklist.objects.count()

        # Delete all handovers first (foreign key dependency)
        HandoverChecklist.objects.all().delete()
        
        # Delete all car requests
        CarRequest.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully deleted {request_count} car requests and {handover_count} handovers'
            )
        )
