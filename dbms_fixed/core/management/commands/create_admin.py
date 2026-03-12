from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a default admin superuser for CTLMS'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin', help='Admin username (default: admin)')
        parser.add_argument('--email', default='admin@gmail.com', help='Admin email')
        parser.add_argument('--password', default='admin', help='Admin password (default: admin)')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'Admin user "{username}" already exists. Skipping.'))
            return

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role=User.Role.ADMIN,
        )
        self.stdout.write(self.style.SUCCESS(f'Superuser "{user.username}" created successfully.'))
