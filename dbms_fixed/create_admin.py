import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ctlms.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = 'admin'
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@gmail.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin')

if User.objects.filter(username=username).exists():
    print(f'Admin user "{username}" already exists. Skipping.')
else:
    User.objects.create_superuser(
        username=username,
        email=email,
        password=password,
        role=User.Role.ADMIN,
    )
    print(f'Superuser "{username}" created successfully.')
