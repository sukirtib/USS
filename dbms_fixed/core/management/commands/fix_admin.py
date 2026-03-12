"""
Fix admin user to have Django superuser privileges.
Run: python manage.py fix_admin
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Ensure admin users have Django superuser privileges'

    def handle(self, *args, **options):
        # Fix all ADMIN role users
        admin_users = User.objects.filter(role='ADMIN')
        fixed = 0
        for user in admin_users:
            if not user.is_staff or not user.is_superuser:
                user.is_staff = True
                user.is_superuser = True
                user.save()
                fixed += 1
                self.stdout.write(self.style.SUCCESS(f'Fixed user: {user.username}'))
        
        if fixed == 0:
            self.stdout.write(self.style.SUCCESS('All admin users already have proper permissions'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Fixed {fixed} admin user(s)'))
