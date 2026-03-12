import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a default admin superuser for CTLMS'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin', help='Admin username (default: admin)')
        parser.add_argument('--email', default=None, help='Admin email')
        parser.add_argument('--password', default=None, help='Admin password')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email'] or os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@gmail.com')
        password = options['password'] or os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin')

        if User.objects.filter(username=username).exists():
            # Ensure existing admin has proper Django admin access
            user = User.objects.get(username=username)
            if not user.is_staff or not user.is_superuser:
                user.is_staff = True
                user.is_superuser = True
                user.role = User.Role.ADMIN
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Updated "{username}" with superuser privileges.'))
            else:
                self.stdout.write(self.style.WARNING(f'Admin user "{username}" already exists. Skipping.'))
            return

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role=User.Role.ADMIN,
        )
        self.stdout.write(self.style.SUCCESS(f'Superuser "{user.username}" created successfully.'))
