from django.core.management.base import BaseCommand
from fleet.models import CarRequest


class Command(BaseCommand):
    help = 'Check pending CEO approval requests'

    def handle(self, *args, **options):
        # Check all pending out-of-town requests
        all_pending = CarRequest.objects.filter(status='pending', out_of_town=True)
        self.stdout.write(f'\n=== All Pending Out-of-Town Requests ===')
        self.stdout.write(f'Total: {all_pending.count()}\n')
        
        for req in all_pending:
            self.stdout.write(f'ID: {req.id}')
            self.stdout.write(f'  Code: {req.request_code}')
            self.stdout.write(f'  Subsidiary: {req.subsidiary}')
            self.stdout.write(f'  Requester: {req.requester.username}')
            self.stdout.write(f'  Approver1 (GM): {req.approver1}')
            self.stdout.write(f'  Approver2 (CEO): {req.approver2}')
            self.stdout.write(f'  Status: {req.status}')
            self.stdout.write('')
        
        # Check what CEO should see
        ceo_should_see = CarRequest.objects.filter(
            status='pending',
            out_of_town=True,
            approver1__isnull=False
        )
        self.stdout.write(f'\n=== CEO Should See (GM Approved) ===')
        self.stdout.write(f'Total: {ceo_should_see.count()}\n')
        
        for req in ceo_should_see:
            self.stdout.write(f'ID: {req.id}, Code: {req.request_code}, Approved by: {req.approver1}')
