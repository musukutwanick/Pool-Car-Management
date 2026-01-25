from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from getpass import getpass

User = get_user_model()


class Command(BaseCommand):
    help = 'Create or update an MIS admin user and associated Profile (role=mis)'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='mis_admin', help='Username for the MIS user')
        parser.add_argument('--email', type=str, default='mis@example.com', help='Email for the MIS user')
        parser.add_argument('--password', type=str, default=None, help='Password for the MIS user (if omitted you will be prompted)')
        parser.add_argument('--superuser', action='store_true', help='Make the created user a Django superuser')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        make_super = options['superuser']

        if password is None:
            password = getpass('Password for MIS user: ')
            confirm = getpass('Confirm password: ')
            if password != confirm:
                self.stderr.write('Passwords do not match. Aborting.')
                return

        try:
            from fleet.models import Profile
        except Exception as e:
            self.stderr.write('Could not import Profile model: %s' % e)
            return

        user, created = User.objects.get_or_create(username=username, defaults={'email': email})
        if created:
            user.set_password(password)
            user.email = email
            user.is_staff = True
            user.is_superuser = make_super
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created user '{username}'"))
        else:
            # Update existing
            user.email = email
            user.is_staff = True
            if make_super:
                user.is_superuser = True
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Updated existing user '{username}'"))

        # Create or update profile
        profile, pcreated = Profile.objects.get_or_create(user=user)
        profile.role = 'mis'
        profile.is_dedicated_driver = False
        # Keep subsidiary as-is (if set) otherwise leave blank
        profile.save()

        self.stdout.write(self.style.SUCCESS(f"MIS role assigned to user '{username}'. is_staff={user.is_staff} is_superuser={user.is_superuser}"))
