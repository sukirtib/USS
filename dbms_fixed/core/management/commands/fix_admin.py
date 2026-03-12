"""
Fix admin user to have Django superuser privileges.
Run: python manage.py fix_admin
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class Command(BaseCommand):
    help = 'Ensure admin users have Django superuser privileges'

    def handle(self, *args, **options):
        # Fix users with role='ADMIN' OR username='admin'
        admin_users = User.objects.filter(Q(role='ADMIN') | Q(username='admin'))
        fixed = 0
        for user in admin_users:
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
                fixed += 1
                self.stdout.write(self.style.SUCCESS(f'Fixed user: {user.username}'))
            else:
                self.stdout.write(f'User {user.username} already OK')
        
        if fixed == 0:
            self.stdout.write(self.style.SUCCESS('All admin users already have proper permissions'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Fixed {fixed} admin user(s)'))
