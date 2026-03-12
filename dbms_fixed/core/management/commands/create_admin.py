import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a default admin superuser for CTLMS'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin')
        parser.add_argument('--email', default=None)
        parser.add_argument('--password', default=None)

    def handle(self, *args, **options):
        username = options['username']
        email = options['email'] or os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@gmail.com')
        password = options['password'] or os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

        user = User.objects.filter(username=username).first()
        if user:
            changed = False
            if not user.is_staff:
                user.is_staff = True
                changed = True
            if not user.is_superuser:
                user.is_superuser = True
                changed = True
            if user.role != 'ADMIN':
                user.role = 'ADMIN'
                changed = True
            if changed:
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Fixed admin privileges for "{user.username}"'))
            else:
                self.stdout.write(self.style.WARNING(f'Admin user "{user.username}" already OK. Skipping.'))
            return

        user = User.objects.create_superuser(
            username=username, email=email, password=password,
            role=User.Role.ADMIN,
        )
        self.stdout.write(self.style.SUCCESS(f'Superuser "{user.username}" created successfully.'))
